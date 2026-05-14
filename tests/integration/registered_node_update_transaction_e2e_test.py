"""
Integration tests for RegisteredNodeUpdateTransaction.
"""

from __future__ import annotations

import time

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_node_address_book_query import RegisteredNodeAddressBookQuery
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
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
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Helper: registered node creation failed: {ResponseCode(receipt.status).name}"
    )
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

        # Allow mirror node to sync
        time.sleep(5)

        # Query the registered node to verify the description was updated
        address_book = RegisteredNodeAddressBookQuery().set_registered_node_id(registered_node_id).execute(admin_client)
        assert len(address_book.nodes) == 1, "Expected exactly one registered node"
        assert address_book.nodes[0].description == "updated description", (
            f"Expected 'updated description' but got {address_book.nodes[0].description!r}"
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

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(999999999)
            .set_description("should fail")
            .freeze_with(admin_client)
            .sign(admin_key)
            .execute(admin_client)
        )
        assert receipt.status == ResponseCode.INVALID_REGISTERED_NODE_ID, (
            f"Expected INVALID_REGISTERED_NODE_ID but got {ResponseCode(receipt.status).name}"
        )
    except PrecheckError:
        pass  # Also acceptable: network rejects at precheck


def test_registered_node_update_admin_key_both_sign(admin_client):
    """Test updating admin key when both old and new keys sign succeeds."""
    old_admin_key = PrivateKey.generate_ed25519()
    new_admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(admin_client, old_admin_key)

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_admin_key(new_admin_key.public_key())
            .freeze_with(admin_client)
            .sign(old_admin_key)
            .sign(new_admin_key)
            .execute(admin_client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update admin key failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup: must sign with the new admin key now
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(admin_client).sign(
            new_admin_key
        ).execute(admin_client)


def test_registered_node_update_admin_key_only_old_signs(admin_client):
    """Test updating admin key when only old key signs fails with INVALID_SIGNATURE."""
    old_admin_key = PrivateKey.generate_ed25519()
    new_admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(admin_client, old_admin_key)

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_admin_key(new_admin_key.public_key())
            .freeze_with(admin_client)
            .sign(old_admin_key)
            .execute(admin_client)
        )
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
            f"Expected INVALID_SIGNATURE but got {ResponseCode(receipt.status).name}"
        )
    except PrecheckError:
        pass  # Also acceptable: network rejects at precheck
    finally:
        # Cleanup: admin key was not changed, so old key still works
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(admin_client).sign(
            old_admin_key
        ).execute(admin_client)


def test_registered_node_update_ip_to_domain_endpoint(admin_client):
    """Test updating a registered node from an IP address endpoint to a domain name endpoint."""
    admin_key = PrivateKey.generate_ed25519()

    # Create registered node with an IP address endpoint
    ip_endpoint = BlockNodeServiceEndpoint(
        ip_address=bytes([10, 0, 0, 1]),
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS],
    )
    receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description("ip endpoint node")
        .set_service_endpoints([ip_endpoint])
        .freeze_with(admin_client)
        .sign(admin_key)
        .execute(admin_client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    registered_node_id = receipt.registered_node_id

    try:
        # Update to a domain name endpoint
        domain_endpoint = BlockNodeServiceEndpoint(
            domain_name="block.updated.com",
            port=443,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.STATUS],
        )
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_service_endpoints([domain_endpoint])
            .freeze_with(admin_client)
            .sign(admin_key)
            .execute(admin_client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Registered node update IP to domain failed with status {ResponseCode(receipt.status).name}"
        )
    finally:
        # Cleanup
        RegisteredNodeDeleteTransaction().set_registered_node_id(registered_node_id).freeze_with(admin_client).sign(
            admin_key
        ).execute(admin_client)
