"""
Example demonstrating comprehensive contract update operations on the network.

This module shows how to update an existing smart contract using ALL available setters:
1. Setting up a client with operator credentials
2. Creating a contract to demonstrate updates on
3. Updating the contract with all possible properties

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    python -m examples.contract_update

"""

import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateTransaction,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp

# Import the bytecode for a basic smart contract (SimpleContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import SIMPLE_CONTRACT_BYTECODE

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


def create_updated_contract_file(client):
    """Create a second file for demonstrating file ID updates"""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("Updated contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"Updated file creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    return file_receipt.file_id


def create_initial_contract(client, file_id):
    """Create the initial contract that we'll update later"""
    receipt = (
        ContractCreateTransaction()
        .set_bytecode_file_id(file_id)
        .set_gas(2000000)  # 2M gas
        .set_contract_memo("Initial contract for update demo")
        .set_admin_key(client.operator_private_key.public_key())
        .execute(client)
    )

    # Check if contract creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    return receipt.contract_id


def contract_update_comprehensive():
    """
    Demonstrates updating a contract with ALL available setters by:
    1. Setting up client with operator account
    2. Creating files containing contract bytecode
    3. Creating an initial contract
    4. Updating the contract using all available setters
    """
    client = setup_client()

    # Create files for bytecode
    file_id = create_contract_file(client)
    updated_file_id = create_updated_contract_file(client)

    # Create initial contract
    contract_id = create_initial_contract(client, file_id)
    print(f"Contract created successfully with ID: {contract_id}")

    # Calculate future expiration time (1 year from now)
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    expiration_time = Timestamp.from_date(future_date)

    # Update contract using ALL available setters
    receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)                                    # Required: Contract to update
        .set_contract_memo("Updated with ALL setters!")                  # Update memo
        .set_admin_key(client.operator_private_key.public_key())         # Update admin key
        .set_expiration_time(expiration_time)                           # Set expiration to 1 year from now
        .set_auto_renew_period(Duration(180 * 24 * 60 * 60))           # 180 days auto-renew
        .set_file_id(updated_file_id)                                   # Update bytecode file
        .set_max_automatic_token_associations(50)                       # Allow 50 token associations
        .set_auto_renew_account_id(client.operator_account_id)          # Set auto-renew payer
        .set_staked_node_id(0)                                          # Stake to node 0
        .set_decline_reward(False)                                      # Accept staking rewards
        .execute(client)
    )

    # Check if contract update was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract update failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Contract updated successfully! All setters used:")
    print(f"  • Contract ID: {contract_id}")
    print(f"  • New memo: 'Updated with ALL setters!'")
    print(f"  • Admin key: Updated")
    print(f"  • Expiration: {future_date.strftime('%Y-%m-%d')}")
    print(f"  • Auto-renew period: 180 days")
    print(f"  • Bytecode file: {updated_file_id}")
    print(f"  • Max token associations: 50")
    print(f"  • Auto-renew account: {client.operator_account_id}")
    print(f"  • Staked to node: 0")
    print(f"  • Decline rewards: False")


if __name__ == "__main__":
    contract_update_comprehensive()
