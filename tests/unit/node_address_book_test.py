"""
Test cases for the NodeAddressBook class.
"""

from __future__ import annotations

import re

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.address_book.node_address_book import NodeAddressBook
from hiero_sdk_python.hapi.services import basic_types_pb2


# Helper
@pytest.fixture
def node_address():
    """Fixture for the node_address."""
    return NodeAddress(
        public_key="0" * 32,
        account_id=AccountId.from_string("0.0.2"),
        node_id=1,
        cert_hash=("0" * 32).encode("utf-8"),
        addresses=[Endpoint(domain_name="test1.net.in", port=50211)],
        description="Test Node",
    )


def _assert_node_address(node1: NodeAddress, node2: NodeAddress):
    """ "Assert that two NodeAddress instances have same values."""
    assert node1._account_id == node2._account_id
    assert node1._description == node2._description
    assert node1._public_key == node2._public_key
    assert node1._node_id == node2._node_id
    assert node1._cert_hash == node2._cert_hash

    assert len(node1._addresses) == len(node2._addresses)


# __init__()


def test_constuctor_without_params():
    """Test NodeAddressBook constructor without parameters."""
    book = NodeAddressBook()
    assert book is not None
    assert book.node_addresses is not None
    assert len(book.node_addresses) == 0


def test_constuctor_with_params(node_address):
    """Test NodeAddressBook constructor with parameters."""
    node_addresses = [node_address]
    book = NodeAddressBook(node_addresses=node_addresses)
    assert book is not None
    assert book.node_addresses is not None
    assert len(book.node_addresses) == 1
    assert book.node_addresses is not node_addresses

    _assert_node_address(book.node_addresses[0], node_addresses[0])


@pytest.mark.parametrize(
    "node_addresses",
    [
        {},
        "node_addresses",
        1,
        True,
        0.1,
    ],
)
def test_constuctor_with_invalid_params(node_addresses):
    """Test NodeAddressBook constructor with invalid parameters."""
    with pytest.raises(TypeError, match=re.escape("node_addresses must be of type list[NodeAddress]")):
        NodeAddressBook(node_addresses=node_addresses)


# set_node_addresses()


def test_set_node_addresses(node_address):
    """Test node_addresses setter."""
    node_addresses = [node_address]
    book = NodeAddressBook().set_node_addresses(node_addresses)

    assert book.node_addresses is not None
    assert len(book.node_addresses) == 1
    assert book.node_addresses is not node_addresses
    _assert_node_address(book.node_addresses[0], node_addresses[0])


@pytest.mark.parametrize("node_addresses", [{}, "node_addresses", 1, True, 0.1, None])
def test_set_node_addresses_with_non_list_type(node_addresses):
    """Test setting node_addresses with invalid types."""
    with pytest.raises(TypeError, match=re.escape("node_addresses must be of type list[NodeAddress]")):
        NodeAddressBook().set_node_addresses(node_addresses)


@pytest.mark.parametrize(
    "node_addresses",
    [
        ["node_address1", "node_address2"],
        [
            NodeAddress(
                public_key="0" * 32,
                account_id=AccountId.from_string("0.0.2"),
                node_id=1,
                cert_hash=("0" * 32).encode("utf-8"),
                addresses=[Endpoint(domain_name="test1.net.in", port=50211)],
                description="Test Node1",
            ),
            "node_address2",
        ],
    ],
)
def test_set_node_addresses_with_invalid_list(node_addresses):
    """Test setting node_addresses with invalid list."""
    with pytest.raises(TypeError, match=re.escape("node_addresses must contain only NodeAddress instances")):
        NodeAddressBook().set_node_addresses(node_addresses)


# protobuf roundtrip


def test_to_proto(node_address):
    """Test to_proto returns basic_types_pb2.NodeAddressBook."""
    node_addresses = [node_address]

    proto = NodeAddressBook(node_addresses=node_addresses)._to_proto()

    assert proto is not None
    assert isinstance(proto, basic_types_pb2.NodeAddressBook)

    assert len(proto.nodeAddress) == 1
    node_address_proto = proto.nodeAddress[0]

    assert isinstance(node_address_proto, basic_types_pb2.NodeAddress)
    assert node_address_proto.nodeAccountId == node_address._account_id._to_proto()
    assert node_address_proto.description == node_address._description
    assert node_address_proto.RSA_PubKey == node_address._public_key
    assert node_address_proto.nodeId == node_address._node_id
    assert node_address_proto.nodeCertHash == node_address._cert_hash

    assert len(node_address_proto.serviceEndpoint) == len(node_address._addresses)


def test_protobuf_roundtrip(node_address):
    """Test protobuf roundtrip."""
    node_addresses = [node_address]

    book1 = NodeAddressBook(node_addresses=node_addresses)
    book2 = NodeAddressBook._from_proto(book1._to_proto())

    assert book1 is not None
    assert book2 is not None

    assert len(book1.node_addresses) == len(book2.node_addresses)
    _assert_node_address(book1.node_addresses[0], book2.node_addresses[0])


# serialization roundtrip


def test_to_bytes(node_address):
    """Test to_bytes return serialize bytes."""
    node_addresses = [node_address]
    data = NodeAddressBook(node_addresses=node_addresses).to_bytes()

    assert data is not None
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_serialization_roundtrip(node_address):
    """Test serialization roundtrip."""
    node_addresses = [node_address]

    book1 = NodeAddressBook(node_addresses=node_addresses)
    book2 = NodeAddressBook.from_bytes(book1.to_bytes())

    assert book1 is not None
    assert book2 is not None

    assert len(book1.node_addresses) == len(book2.node_addresses)
    _assert_node_address(book1.node_addresses[0], book2.node_addresses[0])


@pytest.mark.parametrize("data", ["bytes", 1, True, 0.3, [], {}, None])
def test_from_bytes_invlid_param(data):
    """Test from_bytes invalid parameters raise error."""
    with pytest.raises(TypeError, match="data must be of type bytes"):
        NodeAddressBook.from_bytes(data)
