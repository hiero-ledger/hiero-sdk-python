from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import Mock, patch
from uuid import uuid4

import grpc
import pytest

from hiero_sdk_python import AccountId, Client
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import crypto_get_info_pb2, response_header_pb2, response_pb2
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.response_code import ResponseCode
from tck.errors import HIERO_ERROR, INTERNAL_ERROR, INVALID_PARAMS, JsonRpcError
from tck.handlers import sdk
from tck.handlers.registry import dispatch, get_handler
from tck.param.sdk import PingParams
from tck.server import app
from tck.util.client_utils import remove_client, store_client
from tests.unit.mock_server import MockServer, RealRpcError


pytestmark = pytest.mark.unit


def test_ping_methods_are_registered():
    assert get_handler("ping") is not None
    assert get_handler("pingAll") is not None


def test_ping_params_forward_node_account_id_and_require_session():
    params = PingParams.parse_json_params({"sessionId": "s", "nodeAccountId": "0.0.3"})
    assert params.nodeAccountId == "0.0.3"

    assert PingParams.parse_json_params({"sessionId": "s"}).nodeAccountId is None
    assert PingParams.parse_json_params({"sessionId": "s", "nodeAccountId": " "}).nodeAccountId == " "
    with pytest.raises(ValueError):
        PingParams.parse_json_params({"nodeAccountId": "0.0.3"})


def test_ping_missing_node_account_id_uses_downstream_sdk_validation():
    client = Mock()
    with patch.object(sdk, "get_client", return_value=client), pytest.raises(JsonRpcError) as error:
        dispatch("ping", {"sessionId": "s"})
    assert error.value.code == INTERNAL_ERROR
    assert isinstance(error.value.__cause__, TypeError)
    client.ping.assert_not_called()


@pytest.mark.parametrize("node_account_id", [None, "", " ", "malformed", "0.0.x", 3])
def test_ping_malformed_node_uses_sdk_validation(node_account_id):
    client = Mock()
    with patch.object(sdk, "get_client", return_value=client), pytest.raises(JsonRpcError) as error:
        dispatch("ping", {"sessionId": "s", "nodeAccountId": node_account_id})
    assert error.value.code == INTERNAL_ERROR
    assert isinstance(error.value.__cause__, (TypeError, ValueError))
    client.ping.assert_not_called()


def test_ping_dispatches_and_returns_exact_response():
    client = Mock()
    with patch.object(sdk, "get_client", return_value=client):
        result = dispatch("ping", {"sessionId": "s", "nodeAccountId": "0.0.3"})

    client.ping.assert_called_once_with(AccountId.from_string("0.0.3"))
    assert result == {
        "message": "Successfully pinged node 0.0.3.",
        "status": "SUCCESS",
    }


def test_ping_all_dispatches_and_returns_exact_response():
    client = Mock()
    with patch.object(sdk, "get_client", return_value=client):
        result = dispatch("pingAll", {"sessionId": "s"})

    client.ping_all.assert_called_once_with()
    assert result == {"message": "Successfully pinged all nodes.", "status": "SUCCESS"}


def test_ping_max_attempts_uses_centralized_hiero_error():
    client = Mock()
    client.ping.side_effect = MaxAttemptsError("unreachable", node_id="0.0.3")
    with patch.object(sdk, "get_client", return_value=client), pytest.raises(Exception) as error:
        dispatch("ping", {"sessionId": "s", "nodeAccountId": "0.0.3"})
    assert error.value.code == HIERO_ERROR


def test_ping_all_max_attempts_uses_centralized_hiero_error():
    client = Mock()
    client.ping_all.side_effect = MaxAttemptsError("unreachable", node_id="0.0.3")
    with patch.object(sdk, "get_client", return_value=client), pytest.raises(Exception) as error:
        dispatch("pingAll", {"sessionId": "s"})
    assert error.value.code == HIERO_ERROR


def test_ping_unknown_node_is_internal_error():
    with Client.for_network({"localhost:50211": AccountId(0, 0, 3)}) as client:
        with patch.object(sdk, "get_client", return_value=client), pytest.raises(JsonRpcError) as error:
            dispatch("ping", {"sessionId": "s", "nodeAccountId": "0.0.999"})
        assert error.value.code == INTERNAL_ERROR
        assert error.value.data is None
        assert isinstance(error.value.__cause__, RuntimeError)
        assert str(error.value.__cause__) == "No node found for node_account_id: 0.0.999"


def test_ping_precheck_remains_hiero_error_with_status():
    client = Mock()
    client.ping.side_effect = PrecheckError(status=1, transaction_id=None, message="failure")
    with patch.object(sdk, "get_client", return_value=client), pytest.raises(Exception) as error:
        dispatch("ping", {"sessionId": "s", "nodeAccountId": "0.0.3"})
    assert error.value.code == HIERO_ERROR
    assert error.value.data["status"] == "INVALID_TRANSACTION"


def _cost_response(status=ResponseCode.OK):
    return response_pb2.Response(
        cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=status,
                responseType=ResponseType.COST_ANSWER,
            )
        )
    )


@pytest.fixture
def rpc_network():
    """Register real SDK clients backed by local gRPC servers, isolated per test."""
    with ExitStack() as stack:

        def create(response_sequences):
            servers = []
            for responses in response_sequences:
                server = MockServer(responses)
                stack.callback(server.close)
                servers.append(server)
            client = Client.for_network(
                {server.address: AccountId(0, 0, index + 3) for index, server in enumerate(servers)}
            ).set_max_attempts(1)
            stack.callback(client.close)
            session_id = str(uuid4())
            store_client(session_id, client)
            stack.callback(remove_client, session_id)
            return session_id, servers

        yield create


@pytest.mark.parametrize("method", ["ping", "pingAll"])
def test_ping_http_success_runs_real_sdk_probe(rpc_network, method):
    session_id, servers = rpc_network([[_cost_response()], [_cost_response()]])
    params = {"sessionId": session_id}
    if method == "ping":
        params["nodeAccountId"] = "0.0.4"
    with app.test_client() as http:
        response = http.post("/", json={"jsonrpc": "2.0", "id": 42, "method": method, "params": params})
    assert response.status_code == 200
    assert response.get_json() == {
        "jsonrpc": "2.0",
        "id": 42,
        "result": {
            "status": "SUCCESS",
            "message": "Successfully pinged node 0.0.4." if method == "ping" else "Successfully pinged all nodes.",
        },
    }
    assert [len(server.calls) for server in servers] == ([0, 1] if method == "ping" else [1, 1])
    for server in servers:
        for rpc_method, request in server.calls:
            assert rpc_method == "getAccountInfo"
            assert request.WhichOneof("query") == "cryptoGetInfo"
            assert request.cryptoGetInfo.accountID == AccountId(0, 0, 2)._to_proto()
            assert request.cryptoGetInfo.header.responseType == ResponseType.COST_ANSWER
            assert not request.cryptoGetInfo.header.HasField("payment")


@pytest.mark.parametrize("method", ["ping", "pingAll"])
@pytest.mark.parametrize("failure", ["precheck", "retry_exhaustion", "unavailable", "permission_denied"])
def test_ping_http_errors_use_centralized_mapping_and_stop_probing(rpc_network, method, failure):
    if failure == "precheck":
        failed_response = _cost_response(ResponseCode.INVALID_ACCOUNT_ID)
        expected_error = {"code": HIERO_ERROR, "message": "Hiero error", "data": {"status": "INVALID_ACCOUNT_ID"}}
    elif failure == "retry_exhaustion":
        failed_response = _cost_response(ResponseCode.BUSY)
        expected_error = {"code": HIERO_ERROR, "message": "Hiero error"}
    else:
        status = grpc.StatusCode.UNAVAILABLE if failure == "unavailable" else grpc.StatusCode.PERMISSION_DENIED
        failed_response = RealRpcError(status, "node rejected probe")
        expected_error = {
            "code": HIERO_ERROR if failure == "unavailable" else INTERNAL_ERROR,
            "message": "Hiero error" if failure == "unavailable" else "Internal error",
        }
    session_id, servers = rpc_network([[_cost_response()], [failed_response], [_cost_response()]])
    params = {"sessionId": session_id}
    if method == "ping":
        params["nodeAccountId"] = "0.0.4"
    with app.test_client() as http:
        response = http.post("/", json={"jsonrpc": "2.0", "id": "failed-probe", "method": method, "params": params})
    assert response.status_code == 200
    assert response.get_json() == {"jsonrpc": "2.0", "id": "failed-probe", "error": expected_error}
    assert [len(server.calls) for server in servers] == ([0, 1, 0] if method == "ping" else [1, 1, 0])


@pytest.mark.parametrize("node_params", [{}, {"nodeAccountId": "malformed"}, {"nodeAccountId": "0.0.999"}])
def test_ping_http_invalid_node_never_sends_rpc(rpc_network, node_params):
    session_id, servers = rpc_network([[_cost_response()]])
    with app.test_client() as http:
        response = http.post(
            "/",
            json={"jsonrpc": "2.0", "id": 7, "method": "ping", "params": {"sessionId": session_id, **node_params}},
        )
    assert response.get_json() == {
        "jsonrpc": "2.0",
        "id": 7,
        "error": {"code": INTERNAL_ERROR, "message": "Internal error"},
    }
    assert not servers[0].calls


@pytest.mark.parametrize("method", ["ping", "pingAll"])
def test_ping_http_missing_session_is_invalid_params(method):
    with app.test_client() as http:
        response = http.post(
            "/", json={"jsonrpc": "2.0", "id": 8, "method": method, "params": {"nodeAccountId": "0.0.3"}}
        )
    body = response.get_json()
    assert body["id"] == 8
    assert body["error"]["code"] == INVALID_PARAMS
    assert "result" not in body
