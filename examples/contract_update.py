"""
Example demonstrating contract update operations on the network.

This module shows how to update an existing smart contract by:
1. Setting up a client with operator credentials
2. Creating a contract to demonstrate updates on
3. Updating contract properties (memo, admin key)

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    python -m examples.contract_update

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
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateTransaction,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for the stateful contract which supports updates
# This contract is suitable for demonstrating update functionality  
from .contracts import STATEFUL_CONTRACT_BYTECODE, CONTRACT_DEPLOY_GAS

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network="testnet")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string_ed25519(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_contract_file(client):
    """Create a file containing the contract bytecode"""
    print("Creating file with contract bytecode...")
    
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("Contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    print(f"✓ File created successfully with ID: {file_receipt.file_id}")
    return file_receipt.file_id


def create_initial_contract(client, file_id):
    """Create the initial contract that we'll later update"""
    print("Creating contract with initial settings...")
    
    # Prepare constructor parameters for the StatefulContract
    # The contract's constructor expects a bytes32 parameter
    initial_message = "Initial contract state".encode("utf-8")
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    print(f"✓ Constructor parameters prepared with message: '{initial_message.decode('utf-8')}'")
    
    # Create contract with initial settings
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(constructor_params)
        .set_contract_memo("Initial contract memo")
        .execute(client)
    )

    # Check if contract creation was successful
    if contract_receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"
        )
        sys.exit(1)

    print(f"✓ Contract created successfully with ID: {contract_receipt.contract_id}")
    print("✓ Initial memo set to: 'Initial contract memo'")
    return contract_receipt.contract_id


def update_contract_memo(client, contract_id):
    """Update the contract memo"""
    print("\nUpdating contract memo...")
    new_memo = "Updated contract memo"
    
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_memo(new_memo)
        .execute(client)
    )

    # Check if contract update was successful
    if update_receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract memo update failed with status: {ResponseCode(update_receipt.status).name}"
        )
        sys.exit(1)

    print("✓ Contract memo updated successfully!")
    print(f"✓ New memo: '{new_memo}'")


def update_contract_admin_key(client, contract_id):
    """Update the contract admin key"""
    print("\nUpdating contract admin key...")
    
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(client.operator_private_key.public_key())
        .set_memo("Admin key updated")
        .execute(client)
    )

    # Check if contract update was successful
    if update_receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract admin key update failed with status: {ResponseCode(update_receipt.status).name}"
        )
        sys.exit(1)

    print("✓ Contract admin key updated successfully!")
    print("✓ Memo updated to: 'Admin key updated'")
    print(f"✓ Admin key set to: {client.operator_private_key.public_key()}")


def contract_update():
    """
    Demonstrates updating a contract on the network by:
    1. Setting up client with operator account
    2. Creating a file containing contract bytecode
    3. Creating a contract
    4. Updating the contract memo and admin key
    """
    print("=== Contract Update Example ===")
    print("Setting up client connection...")
    
    client = setup_client()
    print("✓ Client connected to testnet network")
    print(f"✓ Operator account: {client.operator_account_id}")

    file_id = create_contract_file(client)
    contract_id = create_initial_contract(client, file_id)

    # Update contract memo
    update_contract_memo(client, contract_id)

    # Update contract admin key
    update_contract_admin_key(client, contract_id)

    print("\n🎉 Contract update example completed successfully!")
    print(f"📄 Final contract ID: {contract_id}")
    print(f"📁 Bytecode file ID: {file_id}")
    print("🔧 All contract properties have been updated")


if __name__ == "__main__":
    contract_update()