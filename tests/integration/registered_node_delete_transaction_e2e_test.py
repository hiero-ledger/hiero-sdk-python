"""
Integration tests for RegisteredNodeDeleteTransaction (HIP-1137).
"""

from __future__ import annotations

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
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
        .set_description("node for delete test")
        .set_service_endpoints([block_endpoint])
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    return receipt.registered_node_id


def test_registered_node_delete(env):
    """Test creating then deleting a registered node."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(env.client, admin_key)

    receipt = (
        RegisteredNodeDeleteTransaction()
        .set_registered_node_id(registered_node_id)
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node delete failed with status {ResponseCode(receipt.status).name}"
    )


def test_registered_node_delete_invalid_id(env):
    """Test that deleting a nonexistent registered node fails at the network level."""
    admin_key = PrivateKey.generate_ed25519()

    receipt = (
        RegisteredNodeDeleteTransaction()
        .set_registered_node_id(999999999)
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert receipt.status != ResponseCode.SUCCESS, "Delete of nonexistent node should fail"
