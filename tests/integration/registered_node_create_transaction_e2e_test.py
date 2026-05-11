"""
Integration tests for RegisteredNodeCreateTransaction.
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
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode


# Account 0.0.2 is the address book admin on solo networks.
# The private key is the well-known genesis key for local development only.
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


def test_registered_node_create_with_block_endpoint(admin_client):
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
        .freeze_with(admin_client)
        .sign(admin_key)
        .execute(admin_client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None, "registered_node_id should not be None"
    assert receipt.registered_node_id > 0, "registered_node_id should be positive"

    # Cleanup: delete the registered node
    RegisteredNodeDeleteTransaction().set_registered_node_id(receipt.registered_node_id).freeze_with(admin_client).sign(
        admin_key
    ).execute(admin_client)


def test_registered_node_create_with_mixed_endpoints(admin_client):
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
        .freeze_with(admin_client)
        .sign(admin_key)
        .execute(admin_client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None

    # Cleanup
    RegisteredNodeDeleteTransaction().set_registered_node_id(receipt.registered_node_id).freeze_with(admin_client).sign(
        admin_key
    ).execute(admin_client)


def test_registered_node_create_fails_without_endpoints(admin_client):
    """Test that creating a registered node with no endpoints fails at the network level."""
    admin_key = PrivateKey.generate_ed25519()

    with pytest.raises(PrecheckError):
        (
            RegisteredNodeCreateTransaction()
            .set_admin_key(admin_key.public_key())
            .set_description("no endpoints")
            .freeze_with(admin_client)
            .sign(admin_key)
            .execute(admin_client)
        )
