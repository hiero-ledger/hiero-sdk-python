"""
Integration tests for RegisteredNodeCreateTransaction (HIP-1137).
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
from hiero_sdk_python.response_code import ResponseCode


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_create_with_block_endpoint():
    """Test creating a registered node with a BlockNodeServiceEndpoint."""
    network = Network(network="solo")
    client = Client(network)

    # Account 0.0.2 is a special admin account with privileges for network management operations.
    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

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
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None, "registered_node_id should not be None"
    assert receipt.registered_node_id > 0, "registered_node_id should be positive"


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_create_with_mixed_endpoints():
    """Test creating a registered node with multiple endpoint types."""
    network = Network(network="solo")
    client = Client(network)

    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

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
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Registered node create failed with status {ResponseCode(receipt.status).name}"
    )
    assert receipt.registered_node_id is not None


@pytest.mark.skip(reason="HIP-1137 registered node support not yet available on local-node/solo")
def test_registered_node_create_fails_without_endpoints():
    """Test that creating a registered node with no endpoints fails."""
    network = Network(network="solo")
    client = Client(network)

    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

    admin_key = PrivateKey.generate_ed25519()

    with pytest.raises(ValueError, match="at least 1"):
        (
            RegisteredNodeCreateTransaction()
            .set_admin_key(admin_key.public_key())
            .set_description("no endpoints")
            .freeze_with(client)
            .sign(admin_key)
            .execute(client)
        )
