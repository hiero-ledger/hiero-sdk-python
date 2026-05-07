"""
Integration tests for RegisteredNodeUpdateTransaction.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode


_ADMIN_OPERATOR_KEY = PrivateKey.from_string_der(
    "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
)
_ADMIN_ACCOUNT_ID = AccountId(0, 0, 2)


@pytest.fixture
def admin_client():
    """Client with address book admin privileges (0.0.2) for registered node operations."""
    network = Network(network="solo")
    client = Client(network)
    client.set_operator(_ADMIN_ACCOUNT_ID, _ADMIN_OPERATOR_KEY)
    yield client
    client.close()


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


def test_registered_node_update_description(admin_client):
    """Test updating a registered node's description."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(admin_client, admin_key)

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_description("updated description")
            .freeze_with(admin_client)
            .sign(admin_key)
            .execute(admin_client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(admin_client).sign(
            admin_key
        ).execute(admin_client)


def test_registered_node_update_service_endpoints(admin_client):
    """Test replacing a registered node's service endpoints."""
    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(admin_client, admin_key)

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
            .freeze_with(admin_client)
            .sign(admin_key)
            .execute(admin_client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(admin_client).sign(
            admin_key
        ).execute(admin_client)


def test_registered_node_update_invalid_id(admin_client):
    """Test that updating a nonexistent registered node fails at the network level."""
    admin_key = PrivateKey.generate_ed25519()

    # Use a very large ID that is unlikely to exist
    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(999999999)
        .set_description("should fail")
        .freeze_with(admin_client)
        .sign(admin_key)
        .execute(admin_client)
    )

    assert receipt.status != ResponseCode.SUCCESS, "Update of nonexistent node should fail"
