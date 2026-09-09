from __future__ import annotations

import grpc
import pytest

from hiero_sdk_python import AccountId, Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    crypto_get_info_pb2,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.node import _Node
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import MockServer, RealRpcError


pytestmark = pytest.mark.unit


def _response(status=ResponseCode.OK, cost=0, account_info=False):
    info = (
        crypto_get_info_pb2.CryptoGetInfoResponse.AccountInfo(key=basic_types_pb2.Key(ed25519=b"\x00" * 32))
        if account_info
        else None
    )
    return response_pb2.Response(
        cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=status,
                responseType=ResponseType.COST_ANSWER,
                cost=cost,
            ),
            accountInfo=info,
        )
    )


def _client(servers):
    nodes = [_Node(AccountId(0, 0, index + 3), server.address, None) for index, server in enumerate(servers)]
    network = Network(nodes=nodes)
    network.set_transport_security(False)
    network.set_verify_certificates(False)
    client = Client(network).set_max_attempts(1).set_min_backoff(0).set_max_backoff(0)
    return client, nodes


def test_ping_sends_only_cost_answer_get_account_info_without_operator():
    server = MockServer([_response(cost=0)])
    client, _ = _client([server])
    try:
        client.ping(AccountId(0, 0, 3))
        assert len(server.calls) == 1
        assert server.calls[0][0] == "getAccountInfo"
        request = server.calls[0][1]
        assert request.cryptoGetInfo.accountID == AccountId(0, 0, 2)._to_proto()
        assert request.cryptoGetInfo.header.responseType == ResponseType.COST_ANSWER
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
        with pytest.raises(ValueError, match="not in the client's network map"):
            client.ping(AccountId(0, 0, 999))
        assert len(first.calls) == 0
    finally:
        client.close()
        first.close()
        second.close()


def test_ping_transport_failure_marks_node_unhealthy_and_recovers():
    server = MockServer(
        [
            RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
            _response(),
            _response(),
            _response(account_info=True),
            _response(account_info=True),
        ]
    )
    client, nodes = _client([server])
    node = nodes[0]
    try:
        with pytest.raises(MaxAttemptsError):
            client.ping(node._account_id)
        assert not node.is_healthy()
        assert node not in client.network._healthy_nodes

        client.ping(node._account_id)
        assert node.is_healthy()
        assert node in client.network._healthy_nodes
        assert node._bad_grpc_response_count == 0
        assert node._current_backoff == node._min_backoff

        client.set_operator(AccountId(0, 0, 1800), PrivateKey.generate())
        AccountInfoQuery(AccountId(0, 0, 2)).execute(client)
        assert [call[1].cryptoGetInfo.header.responseType for call in server.calls[-2:]] == [
            ResponseType.COST_ANSWER,
            ResponseType.ANSWER_ONLY,
        ]
    finally:
        client.close()
        server.close()


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
        with pytest.raises(MaxAttemptsError):
            client.ping_all()
        assert len(servers[0].calls) == 1
        assert len(servers[1].calls) == 1
        assert not servers[2].calls
    finally:
        client.close()
        for server in servers:
            server.close()


def test_ping_all_probes_every_node_successfully():
    servers = [MockServer([_response()]) for _ in range(3)]
    client, _ = _client(servers)
    try:
        client.ping_all()

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
