"""
Demonstrates the full lifecycle of a registered node on the Hedera network.

This example shows how to:
1. Create a registered node with BlockNodeServiceEndpoint and multiple endpoint APIs
2. Query the registered node via the mirror node REST API
3. Update the registered node's description and service endpoints
4. Associate / disassociate the registered node with a consensus node
5. Delete the registered node

NOTE: This is a privileged transaction. Regular developers do not have the required
permissions to manage registered nodes on testnet or mainnet as this operation
requires special authorization.

This example is provided to demonstrate the API for educational purposes or for use
in private network deployments where you have the necessary administrative privileges.
"""

import sys
import time

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_node_address_book_query import RegisteredNodeAddressBookQuery
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
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
    """Demonstrates create, query, update, associate, disassociate, and delete of a registered node."""
    client = setup_client()

    # Generate an admin key for the registered node
    admin_key = PrivateKey.generate_ed25519()

    # ── Step 1: Create a registered node ────────────────────────────
    print("\n--- Step 1: Creating registered node ---")

    block_endpoint = BlockNodeServiceEndpoint(
        ip_address=bytes([127, 0, 0, 1]),
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS, BlockNodeApi.SUBSCRIBE_STREAM],
    )

    try:
        receipt = (
            RegisteredNodeCreateTransaction()
            .set_admin_key(admin_key.public_key())
            .set_description("My Block Node")
            .set_service_endpoints([block_endpoint])
            .freeze_with(client)
            .sign(admin_key)
            .execute(client)
        )
    except (PrecheckError, ValueError) as e:
        print(f"Registered node creation failed: {e}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    registered_node_id = receipt.registered_node_id
    print(f"Registered node created with ID: {registered_node_id}")

    # ── Step 2: Query the registered node via mirror node ───────────
    print("\n--- Step 2: Querying registered node via mirror node ---")

    # Wait for mirror node ingestion
    time.sleep(5)

    try:
        address_book = RegisteredNodeAddressBookQuery().set_registered_node_id(registered_node_id).execute(client)

        if len(address_book) > 0:
            node = address_book[0]
            print(f"Fetched registered node: {node}")
            print(f"  Description: {node.description}")
            print(f"  Endpoints: {len(node.service_endpoints)}")
        else:
            print("No registered nodes returned (mirror may still be ingesting)")
    except RuntimeError as e:
        print(f"Query failed (mirror node may not support this endpoint): {e}")

    # ── Step 3: Update the registered node ──────────────────────────
    print("\n--- Step 3: Updating registered node ---")

    update_endpoint = BlockNodeServiceEndpoint(
        domain_name="block-node.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.STATUS],
    )

    try:
        receipt = (
            RegisteredNodeUpdateTransaction()
            .set_registered_node_id(registered_node_id)
            .set_description("My Updated Block Node")
            .set_service_endpoints([block_endpoint, update_endpoint])
            .freeze_with(client)
            .sign(admin_key)
            .execute(client)
        )
    except (PrecheckError, ValueError) as e:
        print(f"Registered node update failed: {e}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node update failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Registered node updated successfully")

    # ── Step 4: Associate registered node with consensus node ───────
    print("\n--- Step 4: Associating registered node with consensus node 0 ---")

    try:
        receipt = (
            NodeUpdateTransaction()
            .set_node_id(0)
            .add_associated_registered_node(registered_node_id)
            .freeze_with(client)
            .execute(client)
        )
    except (PrecheckError, ValueError) as e:
        print(f"Association failed: {e}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Association failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Registered node {registered_node_id} associated with consensus node 0")

    # ── Step 5: Disassociate registered node from consensus node ────
    print("\n--- Step 5: Disassociating registered node from consensus node 0 ---")

    try:
        receipt = (
            NodeUpdateTransaction()
            .set_node_id(0)
            .clear_associated_registered_nodes()
            .freeze_with(client)
            .execute(client)
        )
    except (PrecheckError, ValueError) as e:
        print(f"Disassociation failed: {e}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Disassociation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Registered node {registered_node_id} disassociated from consensus node 0")

    # ── Step 6: Delete the registered node ──────────────────────────
    print("\n--- Step 6: Deleting registered node ---")

    try:
        receipt = (
            RegisteredNodeDeleteTransaction()
            .set_registered_node_id(registered_node_id)
            .freeze_with(client)
            .sign(admin_key)
            .execute(client)
        )
    except (PrecheckError, ValueError) as e:
        print(f"Registered node deletion failed: {e}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Registered node deletion failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Registered node deleted successfully")
    print("\n--- Registered node lifecycle complete! ---")


if __name__ == "__main__":
    registered_node_lifecycle()
