from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.address_book.registered_node_address_book import RegisteredNodeAddressBook
from hiero_sdk_python.address_book.registered_node_address_book_query import (
    RegisteredNodeAddressBookQuery,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_key():
    """Return a fresh Ed25519 key pair for testing."""
    private = PrivateKey.generate()
    return private.public_key()


def _block_endpoint() -> BlockNodeServiceEndpoint:
    return BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.PUBLISH, BlockNodeApi.SUBSCRIBE_STREAM],
    )


def _mirror_endpoint() -> MirrorNodeServiceEndpoint:
    return MirrorNodeServiceEndpoint(
        domain_name="mirror.example.com",
        port=5600,
        requires_tls=True,
    )


def _rpc_relay_endpoint() -> RpcRelayServiceEndpoint:
    return RpcRelayServiceEndpoint(
        domain_name="rpc.example.com",
        port=8545,
        requires_tls=False,
    )


def _general_endpoint() -> GeneralServiceEndpoint:
    return GeneralServiceEndpoint(
        domain_name="general.example.com",
        port=9000,
        requires_tls=False,
        description="general node",
    )


# ---------------------------------------------------------------------------
# RegisteredNode
# ---------------------------------------------------------------------------


class TestRegisteredNode:
    def test_from_proto_minimal(self):
        proto = RegisteredNodeProto(registered_node_id=42)
        node = RegisteredNode._from_proto(proto)
        assert node.registered_node_id == 42
        assert node.admin_key is None
        assert node.description is None
        assert node.service_endpoints == ()

    def test_from_proto_with_admin_key(self):
        pub = _make_key()
        proto = RegisteredNodeProto(
            registered_node_id=1,
            admin_key=pub._to_proto(),
        )
        node = RegisteredNode._from_proto(proto)
        assert node.admin_key is not None
        assert node.admin_key.to_bytes_raw() == pub.to_bytes_raw()

    def test_from_proto_with_description(self):
        proto = RegisteredNodeProto(
            registered_node_id=5,
            description="test node",
        )
        node = RegisteredNode._from_proto(proto)
        assert node.description == "test node"

    def test_from_proto_with_service_endpoints(self):
        block_ep = _block_endpoint()
        mirror_ep = _mirror_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[block_ep._to_proto(), mirror_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert len(node.service_endpoints) == 2

    def test_from_proto_block_node_endpoint_type(self):
        block_ep = _block_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[block_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], BlockNodeServiceEndpoint)

    def test_from_proto_mirror_node_endpoint_type(self):
        mirror_ep = _mirror_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[mirror_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], MirrorNodeServiceEndpoint)

    def test_from_proto_rpc_relay_endpoint_type(self):
        rpc_ep = _rpc_relay_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[rpc_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], RpcRelayServiceEndpoint)

    def test_from_proto_general_endpoint_type(self):
        gen_ep = _general_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[gen_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], GeneralServiceEndpoint)

    def test_to_proto_round_trip(self):
        pub = _make_key()
        mirror_ep = _mirror_endpoint()
        node = RegisteredNode(
            registered_node_id=7,
            admin_key=pub,
            description="round-trip",
            service_endpoints=(mirror_ep,),
        )
        proto = node._to_proto()
        restored = RegisteredNode._from_proto(proto)
        assert restored.registered_node_id == 7
        assert restored.admin_key.to_bytes_raw() == pub.to_bytes_raw()
        assert restored.description == "round-trip"
        assert len(restored.service_endpoints) == 1

    def test_rejects_zero_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=0)

    def test_rejects_negative_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=-3)

    def test_rejects_non_int_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id="abc")  # type: ignore[arg-type]

    def test_rejects_bool_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=True)

    def test_immutable_service_endpoints(self):
        node = RegisteredNode(registered_node_id=1, service_endpoints=[_mirror_endpoint()])
        assert isinstance(node.service_endpoints, tuple)

    def test_repr(self):
        node = RegisteredNode(registered_node_id=42, description="hello")
        r = repr(node)
        assert "42" in r
        assert "hello" in r


# ---------------------------------------------------------------------------
# RegisteredNodeAddressBook
# ---------------------------------------------------------------------------


class TestRegisteredNodeAddressBook:
    def test_empty(self):
        book = RegisteredNodeAddressBook()
        assert len(book) == 0
        assert list(book) == []

    def test_multiple_nodes(self):
        nodes = (
            RegisteredNode(registered_node_id=1),
            RegisteredNode(registered_node_id=2),
            RegisteredNode(registered_node_id=3),
        )
        book = RegisteredNodeAddressBook(nodes=nodes)
        assert len(book) == 3
        assert book[0].registered_node_id == 1
        assert book[2].registered_node_id == 3

    def test_iteration(self):
        nodes = (
            RegisteredNode(registered_node_id=10),
            RegisteredNode(registered_node_id=20),
        )
        book = RegisteredNodeAddressBook(nodes=nodes)
        ids = [n.registered_node_id for n in book]
        assert ids == [10, 20]

    def test_len(self):
        book = RegisteredNodeAddressBook(nodes=(RegisteredNode(registered_node_id=1),))
        assert len(book) == 1

    def test_repr(self):
        book = RegisteredNodeAddressBook(
            nodes=(RegisteredNode(registered_node_id=1), RegisteredNode(registered_node_id=2))
        )
        assert "2" in repr(book)

    def test_nodes_property_is_tuple(self):
        book = RegisteredNodeAddressBook(nodes=[RegisteredNode(registered_node_id=1)])
        assert isinstance(book.nodes, tuple)


# ---------------------------------------------------------------------------
# RegisteredNodeAddressBookQuery
# ---------------------------------------------------------------------------


class TestRegisteredNodeAddressBookQuery:
    def test_importable(self):
        q = RegisteredNodeAddressBookQuery()
        assert q is not None

    def test_execute_raises_not_implemented(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(NotImplementedError, match="mirror node API support"):
            q.execute()

    def test_error_message_is_clear(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(NotImplementedError) as exc_info:
            q.execute()
        msg = str(exc_info.value)
        assert "RegisteredNodeAddressBookQuery" in msg
        assert "not yet available" in msg

    def test_set_max_registered_node_count(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_max_registered_node_count(10)
        assert result is q  # chaining

    def test_set_max_registered_node_count_rejects_zero(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(0)

    def test_set_max_registered_node_count_rejects_negative(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(-1)

    def test_set_max_registered_node_count_rejects_bool(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(True)

    def test_set_max_registered_node_count_rejects_float(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(1.0)

    def test_set_max_registered_node_count_rejects_string(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count("10")
