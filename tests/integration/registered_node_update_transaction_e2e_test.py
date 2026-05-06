"""
Integration tests for RegisteredNodeUpdateTransaction (HIP-1137).
"""

from __future__ import annotations

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode


def _create_registered_node(client, admin_key):
    """Helper: create a registered node and return its ID."""
    block_endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS],
    )
    receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description("node for update test")
        .set_service_endpoints([block_endpoint])
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    return receipt.registered_node_id


def test_registered_node_update_description(env):
    """Test updating a registered node's description."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env.client, admin_key)

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_description("updated description")
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(env.client).sign(
            admin_key
        ).execute(env.client)


def test_registered_node_update_service_endpoints(env):
    """Test replacing a registered node's service endpoints."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env.client, admin_key)

    try:
        new_endpoint = MirrorNodeServiceEndpoint(
            domain_name="mirror.updated.com",
            port=5600,
            requires_tls=True,
        )

        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_service_endpoints([new_endpoint])
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(env.client).sign(
            admin_key
        ).execute(env.client)


def test_registered_node_update_invalid_id(env):
    """Test that updating a nonexistent registered node fails at the network level."""
    admin_key = PrivateKey.generate_ed25519()

    # Use a very large ID that is unlikely to exist
    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(999999999)
        .set_description("should fail")
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert receipt.status != ResponseCode.SUCCESS, "Update of nonexistent node should fail"
