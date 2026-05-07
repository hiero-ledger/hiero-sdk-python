"""
Demonstrates the full lifecycle of a registered node on the Hedera network.

This example shows how to:
1. Create a registered node with BlockNodeServiceEndpoint and multiple endpoint APIs
2. Update the registered node's description and service endpoints
3. Delete the registered node

NOTE: This is a privileged transaction. Regular developers do not have the required
permissions to manage registered nodes on testnet or mainnet as this operation
requires special authorization.

This example is provided to demonstrate the API for educational purposes or for use
in private network deployments where you have the necessary administrative privileges.
"""

import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode


def setup_client():
    """Initialize and set up the client with operator account."""
    load_dotenv()
    network = Network(network="solo")
    client = Client(network)
    print(f"Connecting to Hedera {network} network!")

    # Account 0.0.2 is a special administrative account with
    # elevated privileges for network management operations.
    # The private key is intentionally public for local development.
    # Note: This setup only works on solo network and will not work on testnet/mainnet.
    original_operator_key = PrivateKey.from_string_der(
        "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137"
    )
    client.set_operator(AccountId(0, 0, 2), original_operator_key)

    return client


def registered_node_lifecycle():
    """Demonstrates create, update, and delete of a registered node."""
    client = setup_client()

    # Generate an admin key for the registered node
    admin_key = PrivateKey.generate_ed25519()

    # ── Step 1: Create a registered node ────────────────────────────
    print("\n--- Creating registered node ---")

    block_endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS, BlockNodeApi.SUBSCRIBE_STREAM],
    )

    receipt = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key.public_key())
        .set_description("Example block node")
        .set_service_endpoints([block_endpoint])
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    registered_node_id = receipt.registered_node_id
    print(f"Registered node created with ID: {registered_node_id}")

    # ── Step 2: Update the registered node ──────────────────────────
    print("\n--- Updating registered node ---")

    mirror_endpoint = MirrorNodeServiceEndpoint(
        domain_name="mirror.example.com",
        port=5600,
        requires_tls=True,
    )

    receipt = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(registered_node_id)
        .set_description("Updated block + mirror node")
        .set_service_endpoints([block_endpoint, mirror_endpoint])
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node update failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Registered node updated successfully")

    # ── Step 3: Delete the registered node ──────────────────────────
    print("\n--- Deleting registered node ---")

    receipt = (
        RegisteredNodeDeleteTransaction()
        .set_registered_node_id(registered_node_id)
        .freeze_with(client)
        .sign(admin_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node deletion failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Registered node deleted successfully")
    print("\n--- Registered node lifecycle complete ---")


if __name__ == "__main__":
    registered_node_lifecycle()
