"""
Example demonstrating schedule deletion on the network.
uv run examples/schedule/schedule_delete_transaction.py
python examples/schedule/schedule_delete_transaction.py
"""

import datetime
import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_delete_transaction import (
    ScheduleDeleteTransaction,
)
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
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


def create_schedule(client, account_id, account_private_key):
    """Create a scheduled transaction"""
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

    # Set expiration time for the scheduled transaction (90 seconds from now)
    expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=90)

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

    print(f"Schedule created with ID: {receipt.schedule_id}")

    return receipt.schedule_id


def schedule_delete():
    """
    Demonstrates schedule deletion functionality by:
    1. Setting up client with operator account
    2. Creating a test account
    3. Creating a scheduled transaction
    4. Deleting the scheduled transaction
    """
    client = setup_client()

    # Create an account first
    account_id, account_private_key = create_account(client)

    # Create a schedule
    schedule_id = create_schedule(client, account_id, account_private_key)

    # Delete the schedule
    print("\nDeleting schedule...")
    receipt = ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Schedule deletion failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(client)
    print(f"Schedule {info.schedule_id} deleted at {info.deleted_at}")


if __name__ == "__main__":
    schedule_delete()
