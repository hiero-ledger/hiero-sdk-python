"""
Example demonstrating contract call query on the network.

This module shows how to query a contract call on the network by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file
4. Querying the contract call

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_call_query
    python -m examples.contract.contract_call_query

"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
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


def create_contract(client, file_id):
    """Create a contract using the file with constructor parameters"""
    initial_message = "Initial message from constructor".encode("utf-8")
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

    return receipt.contract_id


def query_contract_call():
    """
    Demonstrates querying a contract call by:
    1. Setting up client with operator account
    2. Creating a file containing stateful contract bytecode
    3. Creating a contract using the file with constructor parameters
    4. Querying the contract call
    """
    client = setup_client()

    file_id = create_contract_file(client)

    contract_id = create_contract(client, file_id)

    query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(2000000)
        .set_function(
            "getMessageAndOwner"
        )  # Call the contract's getMessageAndOwner() function
    )
    cost = query.get_cost(client)
    query.set_max_query_payment(cost)
    
    result = query.execute(client)
    # You can also use set_function_parameters() instead of set_function() e.g.:
    # .set_function_parameters(ContractFunctionParameters("getMessageAndOwner"))

    # To get data from your contract function results, use the get_* methods
    # with the index that matches the position of each return value.
    #
    # For our function: getMessageAndOwner() returns (bytes32, address)
    # - Use index 0 for the first return value (bytes32 message)
    # - Use index 1 for the second return value (address owner)

    # Get the message (first return value)
    # Use get_bytes32(0) for bytes32 values
    message = result.get_bytes32(0)
    print(f"Message: {message}")

    # Get the owner (second return value)
    # Use get_address(1) for address values
    owner_address = result.get_address(1)
    print(f"Owner: {owner_address}\n")

    # Another way is get result function
    result_function = result.get_result(["bytes32", "address"])
    print(f"Message from get_result function: {result_function[0]}")
    print(f"Owner from get_result function: {result_function[1]}")

    # For different Solidity return types, use these methods:
    #
    # String values:     result.get_string(0)
    # Address values:    result.get_address(1)
    # Number values:     result.get_uint256(2)
    # Boolean values:    result.get_bool(3)
    # Bytes32 values:    result.get_bytes32(4)
    # Bytes values:      result.get_bytes(5)
    #
    # Note: The index number matches the position in your Solidity return statement


if __name__ == "__main__":
    query_contract_call()
