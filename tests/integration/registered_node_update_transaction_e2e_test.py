"""
Integration tests for RegisteredNodeUpdateTransaction (HIP-1137).
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


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_update_description():
    """Test updating a registered node's description."""
    network = Network(network="solo")
    client = Client(network)

    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(client, admin_key)

    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(registered_node_id)
        .set_description("updated description")
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node update failed with status {ResponseCode(receipt.status).name}"
    )


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_update_service_endpoints():
    """Test replacing a registered node's service endpoints."""
    network = Network(network="solo")
    client = Client(network)

    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

    admin_key = PrivateKey.generate_ed25519()
    registered_node_id = _create_registered_node(client, admin_key)

    new_endpoint = MirrorNodeServiceEndpoint(
        domain_name="mirror.updated.com",
        port=5600,
        requires_tls=True,
    )

    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(registered_node_id)
        .set_service_endpoints([new_endpoint])
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node update failed with status {ResponseCode(receipt.status).name}"
    )


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_update_invalid_id():
    """Test that updating a nonexistent registered node fails."""
    network = Network(network="solo")
    client = Client(network)

    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

    admin_key = PrivateKey.generate_ed25519()

    # Use a very large ID that is unlikely to exist
    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(999999999)
        .set_description("should fail")
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    assert receipt.status != ResponseCode.SUCCESS, "Update of nonexistent node should fail"
