from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import grpc
import pytest

from hiero_sdk_python import AccountId, Client, PrivateKey
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import (
    crypto_get_info_pb2,
    crypto_service_pb2_grpc,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.node import _Node
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import MockServer, RealRpcError


pytestmark = pytest.mark.unit


def _response(status=ResponseCode.OK, cost=0):
    return response_pb2.Response(
        cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=status,
                responseType=ResponseType.COST_ANSWER,
                cost=cost,
            ),
        )
    )


def _client(servers):
    nodes = [_Node(AccountId(0, 0, index + 3), server.address, None) for index, server in enumerate(servers)]
    network = Network(nodes=nodes)
    network.set_transport_security(False)
    network.set_verify_certificates(False)
    client = Client(network).set_max_attempts(1).set_min_backoff(0).set_max_backoff(0)
    return client, nodes


class _AccountInfoServer(MockServer):
    """Local gRPC server with a controllable account-info response handler."""

    def __init__(self, handler):
        self.handler = handler
        super().__init__([])

    def _create_mock_servicer(self, servicer_class):
        if servicer_class is not crypto_service_pb2_grpc.CryptoServiceServicer:
            return super()._create_mock_servicer(servicer_class)

        server = self

        class Servicer(crypto_service_pb2_grpc.CryptoServiceServicer):
            def getAccountInfo(self, request, context):
                server.calls.append(("getAccountInfo", request))
                return server.handler(request, context)

        return Servicer()


@pytest.mark.parametrize("with_operator", [False, True])
def test_ping_sends_only_unpaid_cost_answer_get_account_info(with_operator):
    server = MockServer([_response(cost=200_000_000)])
    client, _ = _client([server])
    try:
        if with_operator:
            client.set_operator(AccountId(0, 0, 1800), PrivateKey.generate())
        client.set_default_max_query_payment(0)
        assert client.ping(AccountId(0, 0, 3)) is None
        assert len(server.calls) == 1
        assert server.calls[0][0] == "getAccountInfo"
        request = server.calls[0][1]
        assert request.cryptoGetInfo.accountID == AccountId(0, 0, 2)._to_proto()
        assert request.cryptoGetInfo.header.responseType == ResponseType.COST_ANSWER
        assert not request.cryptoGetInfo.header.HasField("payment")
        assert request.WhichOneof("query") == "cryptoGetInfo"
    finally:
        client.close()
        server.close()


def test_ping_is_pinned_and_unknown_node_does_not_fallback():
    first = MockServer([_response()])
    second = MockServer([_response()])
    client, _ = _client([first, second])
    try:
        client.ping(AccountId(0, 0, 4))
        assert not first.calls
        assert len(second.calls) == 1
        with pytest.raises(RuntimeError, match="No node found for node_account_id: 0.0.999"):
            client.ping(AccountId(0, 0, 999))
        assert len(first.calls) == 0
    finally:
        client.close()
        first.close()
        second.close()


def test_ping_transport_failure_uses_normal_backoff():
    server = MockServer([RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable")])
    client, nodes = _client([server])
    node = nodes[0]
    try:
        with pytest.raises(MaxAttemptsError):
            client.ping(node._account_id)
        assert not node.is_healthy()
        assert node not in client.network._healthy_nodes

        with pytest.raises(RuntimeError, match="All nodes are unhealthy"):
            client.ping(node._account_id)
        assert len(server.calls) == 1
    finally:
        client.close()
        server.close()


@pytest.mark.parametrize(
    "status", [ResponseCode.BUSY, ResponseCode.PLATFORM_NOT_ACTIVE, ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED]
)
def test_ping_retries_transient_precheck_on_requested_node(status):
    other = MockServer([_response()])
    target = MockServer([_response(status), _response()])
    client, _ = _client([other, target])
    client.set_max_attempts(3)
    try:
        assert client.ping(AccountId(0, 0, 4)) is None
        assert not other.calls
        assert len(target.calls) == 2
        for method, request in target.calls:
            assert method == "getAccountInfo"
            assert request.cryptoGetInfo.accountID == AccountId(0, 0, 2)._to_proto()
            assert request.cryptoGetInfo.header.responseType == ResponseType.COST_ANSWER
            assert not request.cryptoGetInfo.header.HasField("payment")
    finally:
        client.close()
        other.close()
        target.close()


def test_ping_retry_exhaustion_preserves_last_precheck():
    server = MockServer([_response(ResponseCode.BUSY) for _ in range(3)])
    client, _ = _client([server])
    client.set_max_attempts(3)
    try:
        with pytest.raises(MaxAttemptsError) as error:
            client.ping(AccountId(0, 0, 3))
        assert len(server.calls) == 3
        assert isinstance(error.value.last_error, PrecheckError)
        assert error.value.last_error.status == ResponseCode.BUSY
    finally:
        client.close()
        server.close()


@pytest.mark.parametrize("status", [grpc.StatusCode.PERMISSION_DENIED, grpc.StatusCode.INVALID_ARGUMENT])
def test_ping_non_retryable_transport_error_is_not_wrapped_or_failed_over(status):
    target = MockServer([RealRpcError(status, "probe rejected"), _response()])
    other = MockServer([_response()])
    client, _ = _client([target, other])
    client.set_max_attempts(3)
    try:
        with pytest.raises(grpc.RpcError) as error:
            client.ping(AccountId(0, 0, 3))
        assert error.value.code() == status
        assert error.value.details() == "probe rejected"
        assert len(target.calls) == 1
        assert not other.calls
    finally:
        client.close()
        target.close()
        other.close()


def test_normal_query_still_skips_a_node_in_backoff():
    unhealthy = MockServer([])
    healthy = MockServer([_response()])
    client, nodes = _client([unhealthy, healthy])
    try:
        client.network._increase_backoff(nodes[0])
        query = AccountInfoQuery(AccountId(0, 0, 2)).set_node_account_ids([nodes[0]._account_id, nodes[1]._account_id])
        query.set_max_attempts(2)._execute(client)
        assert not unhealthy.calls
        assert len(healthy.calls) == 1
    finally:
        client.close()
        unhealthy.close()
        healthy.close()


def test_ping_propagates_precheck_error():
    server = MockServer([_response(ResponseCode.INVALID_ACCOUNT_ID)])
    client, _ = _client([server])
    try:
        with pytest.raises(PrecheckError) as error:
            client.ping(AccountId(0, 0, 3))
        assert error.value.status == ResponseCode.INVALID_ACCOUNT_ID
    finally:
        client.close()
        server.close()


def test_ping_all_is_sequential_and_stops_at_first_failure():
    servers = [
        MockServer([_response()]),
        MockServer([RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable")]),
        MockServer([_response()]),
    ]
    client, _ = _client(servers)
    try:
        with pytest.raises(MaxAttemptsError) as error:
            client.ping_all()
        assert error.value.last_error.code() == grpc.StatusCode.UNAVAILABLE
        assert error.value.last_error.details() == "unavailable"
        assert len(servers[0].calls) == 1
        assert len(servers[1].calls) == 1
        assert not servers[2].calls
    finally:
        client.close()
        for server in servers:
            server.close()


def test_ping_all_respects_node_backoff():
    servers = [MockServer([_response()]) for _ in range(3)]
    client, nodes = _client(servers)
    try:
        client.network._increase_backoff(nodes[0])
        assert not nodes[0].is_healthy()

        with pytest.raises(RuntimeError, match="All nodes are unhealthy"):
            client.ping_all()

        assert not any(server.calls for server in servers)
    finally:
        client.close()
        for server in servers:
            server.close()


def test_ping_all_probes_every_node_successfully():
    servers = [MockServer([_response()]) for _ in range(3)]
    client, _ = _client(servers)
    try:
        assert client.ping_all() is None

        assert [len(server.calls) for server in servers] == [1, 1, 1]
        for server in servers:
            request = server.calls[0][1]
            assert server.calls[0][0] == "getAccountInfo"
            assert request.WhichOneof("query") == "cryptoGetInfo"
            assert request.cryptoGetInfo.accountID == AccountId(0, 0, 2)._to_proto()
            assert request.cryptoGetInfo.header.responseType == ResponseType.COST_ANSWER
    finally:
        client.close()
        for server in servers:
            server.close()


def test_ping_all_waits_for_response_before_contacting_next_node():
    first_started = Event()
    release_first = Event()
    second_started = Event()

    def first_response(request, context):
        first_started.set()
        if not release_first.wait(timeout=5):
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "test did not release first response")
        return _response()

    def second_response(request, context):
        second_started.set()
        return _response()

    first = _AccountInfoServer(first_response)
    second = _AccountInfoServer(second_response)
    client, _ = _client([first, second])
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(client.ping_all)
            try:
                assert first_started.wait(timeout=5)
                assert not pending.done()
                assert not second_started.wait(timeout=0.1)
            finally:
                release_first.set()
            assert pending.result(timeout=5) is None
        assert second_started.is_set()
        assert len(first.calls) == len(second.calls) == 1
    finally:
        client.close()
        first.close()
        second.close()


def test_ping_honors_client_grpc_deadline():
    request_started = Event()
    release_response = Event()

    def delayed_response(request, context):
        request_started.set()
        release_response.wait(timeout=5)
        return _response()

    server = _AccountInfoServer(delayed_response)
    client, nodes = _client([server])
    client.set_grpc_deadline(0.2)
    try:
        with pytest.raises(MaxAttemptsError) as error:
            client.ping(nodes[0]._account_id)
        assert request_started.is_set()
        assert isinstance(error.value.last_error, grpc.RpcError)
        assert error.value.last_error.code() == grpc.StatusCode.DEADLINE_EXCEEDED
        assert len(server.calls) == 1
        assert not nodes[0].is_healthy()
    finally:
        release_response.set()
        client.close()
        server.close()
