"""
Complete network and client setup example with detailed logging.

uv run examples/client/client_network_setup.py
python examples/client/client_network_setup.py
"""
import os
from dotenv import load_dotenv

from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

load_dotenv()


def main():
    """Complete setup of network and client with full configuration details."""
    network_name = os.getenv('NETWORK', 'testnet').lower()
    
    print("=== Network and Client Setup ===\n")
    
    print("Step 1: Create the network configuration")
    network = Network(network_name)
    print(f"Connected to: {network.network}")
    print(f"Nodes available: {len(network.nodes)}")
    
    print("\nStep 2: Create the client with the network")
    client = Client(network)
    print(f"Client initialized with network: {client.network.network}")
    
    print("\nStep 3: Configure operator credentials")
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", "0.0.0"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    
    client.set_operator(operator_id, operator_key)
    print(f"Operator set: {client.operator_account_id}")
    
    print("\n=== Client Configuration ===")
    print(f"Client is ready to use!")
    print(f"Current node: {client.network.current_node._account_id}")
    print(f"Mirror address: {client.network.get_mirror_address()}")
    print(f"Max retry attempts: {client.max_attempts}")
    
    print("\n=== Available Nodes ===")
    for node_id in client.get_node_account_ids():
        print(f"  - Node: {node_id}")
    
    print("\nClient is ready for transactions!")
    
    client.close()


if __name__ == "__main__":
    main()
