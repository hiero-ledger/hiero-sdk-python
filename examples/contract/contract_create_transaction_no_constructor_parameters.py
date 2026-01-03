"""
Example demonstrating contract creation with constructor parameters on the network.

This module shows how to create a stateful smart contract by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file and constructor parameters

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    python -m examples.contract.contract_create_transaction_no_constructor_parameters
    uv run -m examples.contract.contract_create_transaction_no_constructor_parameters

"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for a stateful smart contract (StatefulContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import STATEFUL_CONTRACT_BYTECODE

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
    """Create a file containing the stateful contract bytecode"""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("Stateful contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    return file_receipt.file_id


def contract_create_constructor():
    """
    Demonstrates creating a stateful contract with constructor parameters by:
    1. Setting up client with operator account
    2. Creating a file containing stateful contract bytecode
    3. Creating a contract using the file with constructor parameters
    """
    client = setup_client()

    file_id = create_contract_file(client)

    # Prepare constructor parameters for the stateful contract
    # The contract's constructor expects a bytes32 parameter that will be stored
    # We need to:
    # 1. Convert our string message to UTF-8 bytes (encode)
    # 2. Pass those bytes to add_bytes32() to properly format for the contract
    # NOTE: If message exceeds 32 bytes, it will raise an error.
    # If message is less than 32 bytes, it will be padded with zeros.
    initial_message = "Initial message from constructor".encode("utf-8")

    # Create ContractFunctionParameters object and add the bytes32 parameter
    # This will be passed to setConstructorParameters() when creating the contract
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)

    # Create contract using the file with constructor parameters
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_gas(2000000)  # 2M gas
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(constructor_params)
        .set_contract_memo("Stateful smart contract with constructor")
        .execute(client)
    )

    # Check if contract creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    contract_id = receipt.contract_id
    print(f"Stateful contract created successfully with ID: {contract_id}")
    print(f"Initial message set in constructor: '{initial_message.decode('utf-8')}'")


if __name__ == "__main__":
    contract_create_constructor()
