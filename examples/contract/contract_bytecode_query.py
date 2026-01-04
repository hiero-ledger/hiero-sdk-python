"""
Example demonstrating contract bytecode query on the network.

This module shows how to query a contract bytecode on the network by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file
4. Querying the contract bytecode

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_bytecode_query
    python -m examples.contract.contract_bytecode_query

"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for a simple smart contract (SimpleContract.sol) that can be deployed
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


def create_contract_file(client):
    """Create a file containing the simple contract bytecode"""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("Simple contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    return file_receipt.file_id


def create_contract(client, file_id):
    """Create a contract using the file"""
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_gas(1000000)  # 1M gas
        .set_bytecode_file_id(file_id)
        .set_contract_memo("Simple smart contract")
        .execute(client)
    )

    # Check if contract creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Contract created with ID: {receipt.contract_id}")

    return receipt.contract_id


def query_contract_bytecode():
    """
    Demonstrates querying a contract bytecode by:
    1. Setting up client with operator account
    2. Creating a file containing contract bytecode
    3. Creating a contract using the file
    4. Querying the contract bytecode
    """
    client = setup_client()

    file_id = create_contract_file(client)

    contract_id = create_contract(client, file_id)

    # Retrieve the deployed (runtime) bytecode of the contract from the network via contract id.
    # The result is a bytes object containing the contract's runtime bytecode as stored on-chain.
    bytecode = ContractBytecodeQuery().set_contract_id(contract_id).execute(client)

    # To display the bytecode in a readable hexadecimal string, use the .hex() method.
    print(f"Contract runtime bytecode: {bytecode.hex()}")


if __name__ == "__main__":
    query_contract_bytecode()
