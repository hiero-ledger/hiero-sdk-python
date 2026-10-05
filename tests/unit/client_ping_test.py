from __future__ import annotations

from unittest.mock import patch

import grpc
import pytest

from hiero_sdk_python import AccountId, Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import (
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


def test_ping_transport_failure_retries_when_node_remains_healthy():
    errors = [RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable") for _ in range(3)]
    server = MockServer(errors)
    client, nodes = _client([server])
    client.set_max_attempts(3)
    node = nodes[0]

    try:
        with (
            patch.object(client.network, "_increase_backoff") as increase_backoff,
            pytest.raises(MaxAttemptsError),
        ):
            client.ping(node._account_id)

        assert len(server.calls) == 3
        assert increase_backoff.call_count == 3
        increase_backoff.assert_called_with(node)
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
        completed = []
        original_ping = client.ping

        def ping_and_check_order(node_account_id):
            index = len(completed)
            assert node_account_id == AccountId(0, 0, index + 3)
            assert [len(server.calls) for server in servers] == [int(i < index) for i in range(3)]
            original_ping(node_account_id)
            completed.append(node_account_id)

        with patch.object(client, "ping", side_effect=ping_and_check_order):
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
