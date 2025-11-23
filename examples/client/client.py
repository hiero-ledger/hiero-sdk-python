"""
Complete network and client setup example with detailed logging.

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


def setup_network():
    """Create and configure the network with logging."""
    network_name = os.getenv('NETWORK', 'testnet').lower()
    print("Step 1: Create the network configuration")
    network = Network(network_name)
    print(f"Connected to: {network.network}")
    print(f"Nodes available: {len(network.nodes)}")
    return network


def setup_client(network):
    """Create and initialize the client with the network."""
    print("\nStep 2: Create the client with the network")
    client = Client(network)
    print(f"Client initialized with network: {client.network.network}")
    return client


def setup_operator(client):
    """Configure operator credentials for the client."""
    print("\nStep 3: Configure operator credentials")
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", "0.0.0"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Operator set: {client.operator_account_id}")


def display_client_configuration(client):
    """Display client configuration details."""
    print("\n=== Client Configuration ===")
    print(f"Client is ready to use!")
    print(f"Current node: {client.network.current_node._account_id}")
    print(f"Mirror address: {client.network.get_mirror_address()}")
    print(f"Max retry attempts: {client.max_attempts}")


def display_available_nodes(client):
    """Display all available nodes in the network."""
    print("\n=== Available Nodes ===")
    for node_id in client.get_node_account_ids():
        print(f"  - Node: {node_id}")


def main():
    """Complete setup of network and client with full configuration details."""
    print("=== Network and Client Setup ===\n")
    
    network = setup_network()
    client = setup_client(network)
    setup_operator(client)
    display_client_configuration(client)
    display_available_nodes(client)
    
    print("\nClient is ready for transactions!")
    client.close()


if __name__ == "__main__":
    main()
