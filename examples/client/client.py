"""
Basic client setup and usage example.

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


def main():
    """Create a basic client and display its configuration."""
    network_name = os.getenv('NETWORK', 'testnet').lower()
    
    network = Network(network_name)
    print(f"Connected to: {network.network}")
    print(f"Nodes available: {len(network.nodes)}")
    
    client = Client(network)
    print(f"Client initialized with network: {client.network.network}")
    
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", "0.0.0"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    
    client.set_operator(operator_id, operator_key)
    print(f"Operator set: {client.operator_account_id}")
    
    print(f"\nClient is ready to use!")
    print(f"Current node: {client.network.current_node._account_id}")
    print(f"Mirror address: {client.network.get_mirror_address()}")
    
    client.close()


if __name__ == "__main__":
    main()
