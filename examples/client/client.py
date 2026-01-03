"""
Complete network and client setup example with detailed logging.

This example demonstrates the internal steps of setting up a client
(Network -> Client -> Operator) which is useful for understanding
the architecture. It also demonstrates the quick `from_env()` method.

Usage:
    uv run examples/client/client.py
    python examples/client/client.py
"""

import os
from dotenv import load_dotenv

from hiero_sdk_python import Client, Network, AccountId, PrivateKey

load_dotenv()


def setup_network():
    """Create and configure the network with logging."""
    network_name = os.getenv("NETWORK", "testnet").lower()

    print("Step 1: Create the network configuration")
    network = Network(network_name)

    print(f"  - Connected to: {network.network}")
    print(f"  - Nodes available: {len(network.nodes)}")

    return network


def setup_client(network):
    """Create and initialize the client with the network."""
    print("\nStep 2: Create the client with the network")
    client = Client(network)

    print(f"  - Client initialized with network: {client.network.network}")
    return client


def setup_operator(client):
    """Configure operator credentials for the client."""
    print("\nStep 3: Configure operator credentials")

    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")

    if not operator_id_str or not operator_key_str:
        print("  - ⚠️ OPERATOR_ID or OPERATOR_KEY missing in environment.")
        return

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)

    client.set_operator(operator_id, operator_key)
    print(f"  - Operator set: {client.operator_account_id}")


def display_client_configuration(client):
    """Display client configuration details."""
    print("\n=== Client Configuration ===")
    print(f"Client is ready to use!")
    print(f"Max retry attempts: {client.max_attempts}")

    nodes = client.get_node_account_ids()
    print(f"Total Nodes: {len(nodes)}")


def display_available_nodes(client):
    """Display a sample of available nodes in the network."""
    print("\n=== Available Nodes (Sample) ===")
    nodes = client.get_node_account_ids()

    # showing first 5 Nodes
    for i, node_id in enumerate(nodes[:5]):
        print(f"  - Node: {node_id}")

    if len(nodes) > 5:
        print(f"  ... and {len(nodes) - 5} more.")


def demonstrate_manual_setup():
    """Run the detailed, step-by-step setup."""
    print("\n--- [ Method 1: Manual Setup] ---")
    network = setup_network()
    client = setup_client(network)
    setup_operator(client)
    display_client_configuration(client)
    display_available_nodes(client)
    client.close()


def demonstrate_fast_setup():
    """Run the quick setup used in production."""
    print("\n--- [ Method 2: Fast Setup (from_env) ] ---")
    print("Initializing client from environment variables...")
    try:
        client = Client.from_env()
        print(f"✅ Success! Connected as operator: {client.operator_account_id}")
        client.close()
    except Exception as e:
        print(f"❌ Failed: {e}")


def main():
    # 1. Run the verbose example
    demonstrate_manual_setup()

    # 2. Run the concise example (Best Practice)
    demonstrate_fast_setup()


if __name__ == "__main__":
    main()
