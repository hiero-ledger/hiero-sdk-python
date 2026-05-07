"""
Integration tests for RegisteredNodeCreateTransaction.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode


def test_registered_node_create_with_block_endpoint(env):
    """Test creating a registered node with a BlockNodeServiceEndpoint."""
    admin_key = PrivateKey.generate_ed25519()

    block_endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS, BlockNodeApi.SUBSCRIBE_STREAM],
    )

    receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description("test registered node")
        .set_service_endpoints([block_endpoint])
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None, "registered_node_id should not be None"
    assert receipt.registered_node_id > 0, "registered_node_id should be positive"

    # Cleanup: delete the registered node
    RegisteredNodeDeleteTransaction().set_registered_node_id(receipt.registered_node_id).freeze_with(env.client).sign(
        admin_key
    ).execute(env.client)


def test_registered_node_create_with_mixed_endpoints(env):
    """Test creating a registered node with multiple endpoint types."""
    admin_key = PrivateKey.generate_ed25519()

    block_endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.PUBLISH],
    )
    mirror_endpoint = MirrorNodeServiceEndpoint(
        domain_name="mirror.example.com",
        port=5600,
        requires_tls=True,
    )

    receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description("mixed endpoints node")
        .set_service_endpoints([block_endpoint, mirror_endpoint])
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None

    # Cleanup
    RegisteredNodeDeleteTransaction().set_registered_node_id(receipt.registered_node_id).freeze_with(env.client).sign(
        admin_key
    ).execute(env.client)


def test_registered_node_create_fails_without_endpoints(env):
    """Test that creating a registered node with no endpoints fails (client-side validation)."""
    admin_key = PrivateKey.generate_ed25519()

    with pytest.raises(ValueError, match="at least 1"):
        (
            RegisteredNodeCreateTransaction()
            .set_admin_key(admin_key.public_key())
            .set_description("no endpoints")
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )
