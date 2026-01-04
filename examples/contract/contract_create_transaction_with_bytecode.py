"""
Example demonstrating contract creation on the network.

This module shows how to create a smart contract by:
1. Setting up a client with operator credentials
2. Creating a contract using the bytecode

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_create_transaction_with_bytecode
    python -m examples.contract.contract_create_transaction_with_bytecode

"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for a basic smart contract (SimpleContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import SIMPLE_CONTRACT_BYTECODE

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def contract_create_with_bytecode():
    """
    Demonstrates creating a contract on the network by:
    1. Setting up client with operator account
    2. Creating a contract using the bytecode
    """
    client = setup_client()

    # Convert the contract bytecode from hex string to bytes format
    # This is required because set_bytecode() expects bytes, not a hex string
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)

    # Create contract using the bytecode
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytecode)
        .set_gas(2000000)  # 2M gas
        .set_contract_memo("My first smart contract")
        .execute(client)
    )

    # Check if contract creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    contract_id = receipt.contract_id
    print(f"Contract created successfully with ID: {contract_id}")


if __name__ == "__main__":
    contract_create_with_bytecode()
