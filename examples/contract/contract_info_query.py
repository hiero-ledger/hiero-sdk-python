"""
Example demonstrating contract info query on the network.

This module shows how to query a contract info on the network by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file
4. Querying the contract info

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_info_query
    python -m examples.contract.contract_info_query

"""

import sys
from hiero_sdk_python import Client, Duration
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for a simple smart contract (SimpleContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import SIMPLE_CONTRACT_BYTECODE

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
        .set_initial_balance(1000)  # 1000 tinybars
        .set_max_automatic_token_associations(10)
        .set_auto_renew_account_id(client.operator_account_id)
        .set_auto_renew_period(Duration(seconds=5184000))  # 60 days in seconds
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

def query_contract_info():
    """
    Demonstrates querying a contract info by:
    1. Setting up client with operator account
    2. Creating a file containing contract bytecode
    3. Creating a contract using the file
    4. Querying the contract info
    """
    client = Client.from_env()
    print(f"Operator: {client.operator_account_id}")

    file_id = create_contract_file(client)

    contract_id = create_contract(client, file_id)

    # Query the contract info
    info = ContractInfoQuery().set_contract_id(contract_id).execute(client)

    print("\nContract Info:")
    print(f"Contract ID: {info.contract_id}")
    print(f"Account ID: {info.account_id}")
    print(f"Contract Account ID: {info.contract_account_id}")
    print(f"Admin Key: {info.admin_key}")
    print(f"Auto Renew Account ID: {info.auto_renew_account_id}")
    print(f"Contract Memo: {info.contract_memo}")
    print(f"Balance: {info.balance}")
    print(f"Expiration Time: {info.expiration_time}")
    print(f"Is Deleted: {info.is_deleted}")
    print(f"Ledger ID: {info.ledger_id}")
    print(f"Max Automatic Token Associations: {info.max_automatic_token_associations}")
    print(f"Token Relationships: {info.token_relationships}")

if __name__ == "__main__":
    query_contract_info()
