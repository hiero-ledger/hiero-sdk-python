"""


Example demonstrating contract deletion on the network.

This module shows how to delete a smart contract by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating 2 contracts using the file
4. Deleting the first contract and transferring the hbars to the second contract
5. Checking if the first contract is deleted and the second contract has the hbars
6. Deleting the second contract and transferring the hbars to the operator account
7. Checking if the second contract is deleted

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_delete_transaction
    python -m examples.contract.contract_delete_transaction
"""

import sys



from hiero_sdk_python import Client

from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_delete_transaction import (
    ContractDeleteTransaction,
)
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode

# Import the bytecode for a basic smart contract (SimpleContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import SIMPLE_CONTRACT_BYTECODE



def setup_client() -> Client:
    """
    Set up and configure the client by loading OPERATOR_ID and OPERATOR_KEY with Client.from_env().
    """
    client = Client.from_env()
    print(f"Connecting to Hedera {client.network.network} network!")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_contract_file(client):
    """Create a file containing the contract bytecode."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("Contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    return file_receipt.file_id


def create_contract(client, file_id, initial_balance):
    """Create a contract using the file."""
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_initial_balance(initial_balance)
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


def contract_delete():
    """
    Demonstrates deleting a contract on the network by:

    1. Setting up client with operator account
    2. Creating a file containing contract bytecode
    3. Creating two contracts: one with balance, one for transfer
    4. Deleting the contract and transferring the hbars to a transfer contract
    5. Checking if the contract is deleted and the transfer contract has the hbars
    6. Deleting the transfer contract and transferring the hbars to the operator account
    7. Checking if the transfer contract is deleted.
    """
    client = setup_client()

    file_id = create_contract_file(client)

    # Create contract with initial balance
    initial_balance = Hbar(1).to_tinybars()
    contract_id = create_contract(client, file_id, initial_balance)

    # Create contract with 0 balance that will be used to transfer the hbars
    transfer_contract_id = create_contract(client, file_id, 0)

    # Delete the contract and transfer the hbars to the transfer contract
    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_contract_id(transfer_contract_id)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract deletion failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("\nSuccessfully deleted contract and transferred hbars to transfer contract")

    # Check if the contract is deleted
    contract_info = ContractInfoQuery(contract_id).execute(client)
    print(f"Check contract is deleted: {contract_info.is_deleted}")

    # Check if the transfer contract has the hbars
    transfer_info = ContractInfoQuery(transfer_contract_id).execute(client)
    print(
        f"Check transfer contract balance: {Hbar.from_tinybars(transfer_info.balance)}"
    )

    # Delete the transfer contract and transfer the hbars to the operator account
    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(transfer_contract_id)
        .set_transfer_account_id(client.operator_account_id)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Transfer contract deletion failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(
        "\nSuccessfully deleted transfer contract and transferred hbars to operator account"
    )

    # Check if the transfer contract is deleted
    transfer_info = ContractInfoQuery(transfer_contract_id).execute(client)
    print(f"Check transfer contract is deleted: {transfer_info.is_deleted}")


if __name__ == "__main__":
    contract_delete()
