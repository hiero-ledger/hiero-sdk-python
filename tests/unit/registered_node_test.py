"""Unit tests for the RegisteredNode model."""

from dataclasses import FrozenInstanceError

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)

pytestmark = pytest.mark.unit


def test_registered_node_roundtrip():
    """Registered nodes should round-trip through protobuf."""
    admin_key = KeyList(
        [
            PrivateKey.generate_ed25519().public_key(),
            PrivateKey.generate_ecdsa().public_key(),
        ]
    )
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.STATUS,
    )
    node = RegisteredNode(
        registered_node_id=12,
        admin_key=admin_key,
        description="mirrorable block node",
        service_endpoints=(endpoint,),
    )

    proto = node._to_proto()
    roundtrip = RegisteredNode._from_proto(proto)

    assert isinstance(proto, RegisteredNodeProto)
    assert roundtrip == node


def test_registered_node_is_immutable():
    """Registered nodes should be immutable once constructed."""
    node = RegisteredNode(registered_node_id=12)

    with pytest.raises(FrozenInstanceError):
        node.registered_node_id = 13
