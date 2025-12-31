"""
Complete network and client setup example with detailed logging.

This example demonstrates multiple ways to create a Client: 
1. Traditional setup (Network + Client + set_operator)
2. Client.from_env() - Automatic setup from environment variables
3. Client.for_testnet() / for_mainnet() / for_previewnet() - Network-specific factories

Usage:
    uv run examples/client/client.py
    python examples/client/client.py
"""
import os
from dotenv import load_dotenv

from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

load_dotenv()


def traditional_setup():
    """
    Traditional way to set up a client (for reference).
    This method gives full control over each step.
    """
    print("\n--- Method 1: Traditional Setup ---")

    network_name = os.getenv('NETWORK', 'testnet').lower()
    print(f"Step 1: Creating network configuration for '{network_name}'")
    network = Network(network_name)
    print(f"   Connected to: {network.network}")
    print(f"   Nodes available: {len(network.nodes)}")

    print("Step 2: Creating client with network")
    client = Client(network)

    print("Step 3: Configuring operator credentials")
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", "0.0.0"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"   Operator set:  {client.operator_account_id}")

    return client


def from_env_setup():
    """
    Simplified setup using Client.from_env() - RECOMMENDED. 

    This method automatically: 
    - Reads HEDERA_NETWORK (defaults to "testnet")
    - Reads OPERATOR_ID (required)
    - Reads OPERATOR_KEY (required)
    - Creates and configures the client
    """
    print("\n--- Method 2: Client.from_env() (Recommended) ---")

    # One line to create a fully configured client! 
    client = Client.from_env()

    print(f"✅ Client created with single line!")
    print(f"   Network: {client.network.network}")
    print(f"   Operator: {client.operator_account_id}")

    return client


def network_factory_setup():
    """
    Setup using network-specific factory methods. 

    These methods create a client for a specific network,
    but you still need to set the operator manually.
    Useful when you want to be explicit about which network. 
    """
    print("\n--- Method 3: Network Factory Methods ---")

    # Create clients for different networks
    print("Creating clients for each network...")
    testnet_client = Client.for_testnet()
    mainnet_client = Client.for_mainnet()
    previewnet_client = Client.for_previewnet()

    print(f"   Client.for_testnet() -> {testnet_client.network.network}")
    print(f"   Client.for_mainnet() -> {mainnet_client.network.network}")
    print(f"   Client.for_previewnet() -> {previewnet_client.network.network}")

    # Set operator on testnet client for demo
    print("\nSetting operator on testnet client...")
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", "0.0.0"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    testnet_client.set_operator(operator_id, operator_key)
    print(f"   Operator set:  {testnet_client.operator_account_id}")

    # Clean up other clients
    mainnet_client.close()
    previewnet_client.close()

    return testnet_client


def display_client_configuration(client):
    """Display client configuration details."""
    print("\n=== Client Configuration ===")
    print(f"Network: {client.network.network}")
    print(f"Current node: {client.network.current_node._account_id}")
    print(f"Mirror address: {client.network.get_mirror_address()}")
    print(f"Max retry attempts: {client.max_attempts}")
    print(f"Operator ID: {client.operator_account_id}")
    print(f"TLS enabled: {client.is_transport_security()}")


def display_available_nodes(client):
    """Display all available nodes in the network."""
    print("\n=== Available Nodes ===")
    for node_id in client.get_node_account_ids():
        print(f"  - Node:  {node_id}")


def main():
    """
    Demonstrate different ways to set up a client.
    """
    print("=" * 60)
    print("  Hiero SDK Python - Client Setup Examples")
    print("=" * 60)

    # Method 1: Traditional setup
    client = traditional_setup()
    display_client_configuration(client)
    client.close()

    # Method 2: Using from_env (RECOMMENDED)
    client = from_env_setup()
    display_client_configuration(client)
    display_available_nodes(client)
    client.close()

    # Method 3: Network-specific factory methods
    client = network_factory_setup()
    display_client_configuration(client)
    client.close()

    print("\n" + "=" * 60)
    print("  All examples completed successfully!  ✅")
    print("=" * 60)


if __name__ == "__main__": 
    main()