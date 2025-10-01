"""
Example demonstrating account records query on the network.
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
)
from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network="testnet")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_account(client):
    """Create a test account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(2))
        .set_account_memo("Test account for records query")
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    account_id = receipt.account_id
    print(f"\nAccount created with ID: {account_id}")

    return account_id, account_private_key


def query_account_records():
    """
    Demonstrates the account record query functionality by:
    1. Setting up client with operator account
    2. Creating a new account and setting it as the operator
    3. Querying account records and displaying basic information
    4. Performing a transfer transaction
    5. Querying account records again to see updated transaction history
    """
    client = setup_client()

    # Create a new account
    account_id, account_private_key = create_account(client)

    records_before = AccountRecordsQuery().set_account_id(account_id).execute(client)

    print(f"\nAccount {account_id} has {len(records_before)} transaction records")
    print(f"Transaction records: {records_before}")

    # Set the newly created account as the operator
    client.set_operator(account_id, account_private_key)

    # Perform a transfer transaction from the newly created account to the operator
    receipt = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(client.operator_account_id, Hbar(1).to_tinybars())
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    records_after = AccountRecordsQuery().set_account_id(account_id).execute(client)

    print(f"\nAccount {account_id} has {len(records_after)} transaction record")
    print(f"Transaction records: {records_after}")


if __name__ == "__main__":
    query_account_records()
