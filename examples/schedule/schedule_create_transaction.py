"""
Example demonstrating account schedule creation.
uv run examples/schedule/schedule_create_transaction.py
python examples/schedule/schedule_create_transaction.py
"""

import datetime
import os
import sys
import time

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

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


def create_account(client):
    """Create a test account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(2))
        .set_account_memo("Test account for schedule")
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    account_id = receipt.account_id
    print(f"\nAccount created with ID: {account_id}")

    return account_id, account_private_key


def account_balance(client, account_id):
    """Get the balance of an account"""
    balance = CryptoGetAccountBalanceQuery(account_id).execute(client)
    print(f"Account balance: {balance.hbars} hbars")


def schedule_transfer_transaction(client, account_id):
    """Schedule a transfer transaction"""
    # Amount to transfer in tinybars
    amount = Hbar(1).to_tinybars()
    # Create a transfer transaction
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -amount)
        .add_hbar_transfer(client.operator_account_id, amount)
    )
    # Convert the transfer transaction into a scheduled transaction
    schedule_tx = transfer_tx.schedule()
    return schedule_tx


def schedule_account_create():
    """
    Demonstrates account schedule functionality by:
    1. Setting up client with operator account
    2. Creating a test account
    3. Scheduling a transfer transaction to move HBAR from the test account to the operator account
    4. Signing and executing the scheduled transaction
    5. Checking the account balance before and after the scheduled transaction
    6. Querying the transaction record to check if it was executed
    """
    client = setup_client()

    # Create an account first
    account_id, account_private_key = create_account(client)

    # Schedule a transfer transaction to move HBAR from the test account to the operator account
    schedule_tx = schedule_transfer_transaction(client, account_id)

    # Set expiration time for the scheduled transaction (5 seconds from now)
    expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=5)

    receipt = (
        schedule_tx.set_payer_account_id(
            client.operator_account_id
        )  # payer of the transaction fee
        .set_admin_key(
            client.operator_private_key.public_key()
        )  # delete/modify the transaction
        .set_expiration_time(Timestamp.from_date(expiration_time))
        .set_wait_for_expiry(True)  # wait to expire to execute
        .freeze_with(client)
        .sign(
            account_private_key
        )  # sign with the account private key as it transfers money
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Schedule creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("Transaction scheduled successfully!")
    print(f"Schedule ID: {receipt.schedule_id}")
    print(f"Scheduled Transaction ID: {receipt.scheduled_transaction_id}")
    scheduled_tx_id = receipt.scheduled_transaction_id

    print("\nChecking account balance before scheduled transaction...")
    account_balance(client, account_id)

    time.sleep(5)  # Wait for the scheduled transaction to execute

    print("\nChecking account balance after scheduled transaction...")
    account_balance(client, account_id)

    print("\nQuerying transaction record to check if it was executed...")
    record_query = (
        TransactionRecordQuery().set_transaction_id(scheduled_tx_id).execute(client)
    )
    print(
        f"Transaction Record receipt status: {ResponseCode(record_query.receipt.status).name}"
    )


if __name__ == "__main__":
    schedule_account_create()
