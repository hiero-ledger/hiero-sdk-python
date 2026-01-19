"""
Example demonstrating contract execute on the network.

This module shows how to execute a contract on the network by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file
4. Executing a contract function

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_execute_transaction
    python -m examples.contract.contract_execute_transaction
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_execute_transaction import (
    ContractExecuteTransaction,
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


def create_contract(client, file_id):
    """Create a contract using the file with constructor parameters"""
    initial_message = "This is the initial message!".encode("utf-8")
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
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

    print(f"Contract created with ID: {receipt.contract_id}")

    return receipt.contract_id


def get_contract_message(client, contract_id):
    """Get the message from the contract"""
    # Query the contract function to verify that the message was set
    query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(2000000)
        .set_function("getMessage")
    )

    cost = query.get_cost(client)
    query.set_max_query_payment(cost)
    
    result = query.execute(client)

    # The contract returns bytes32, which we decode to string
    # This removes any padding and converts to readable text
    return result.get_bytes32(0).decode("utf-8")


def execute_contract():
    """
    Demonstrates executing a contract by:
    1. Setting up client with operator account
    2. Creating a file containing stateful contract bytecode
    3. Creating a contract using the file with constructor parameters
    4. Getting the current message from the contract
    5. Executing a contract function to set the new message
    6. Querying the contract function to verify that the message was set
    """
    client = setup_client()

    file_id = create_contract_file(client)

    contract_id = create_contract(client, file_id)

    # Get the current message from the contract
    current_message = get_contract_message(client, contract_id)
    print(f"Initial contract message (from constructor): '{current_message}'")

    new_message_bytes = b"This is the updated message!"
    new_message_string = new_message_bytes.decode("utf-8")  # For display

    # Set the new message from the contract
    receipt = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(2000000)
        .set_function(
            "setMessage",
            ContractFunctionParameters().add_bytes32(new_message_bytes),
        )  # Call the contract's setMessage() function with the parameter b"New message to set"
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract execution failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(
        f"Successfully executed setMessage() on {contract_id} with new message: "
        f"'{new_message_string}'"
    )

    # Query the contract function to verify that the message was set
    updated_message = get_contract_message(client, contract_id)

    print(f"Retrieved message from contract getMessage(): '{updated_message}'")


if __name__ == "__main__":
    execute_contract()
