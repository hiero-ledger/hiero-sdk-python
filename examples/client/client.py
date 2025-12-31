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

def client_example():
    print("Creating client for testnet...")
    client = Client.from_env()
    print(f"Client created for network: {client.network.network}")
    print(f"Operator set: {client.operator_account_id}")
    
    client.close()

if __name__ == "__main__":
    client_example()