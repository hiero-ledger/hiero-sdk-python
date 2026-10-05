from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from hiero_sdk_python import AccountId, Client
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from tck.errors import HIERO_ERROR, INTERNAL_ERROR, JsonRpcError
from tck.handlers import sdk
from tck.handlers.registry import dispatch, get_handler
from tck.param.sdk import PingParams


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
