"""
Example demonstrating account update functionality.
run with:
uv run examples/account/account_update_transaction.py
python examples/account/account_update_transaction.py
"""

import datetime
import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Duration, Hbar, Network, PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp

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
        .set_initial_balance(Hbar(1))
        .set_account_memo("Test account for update")
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


def query_account_info(client, account_id):
    """Query and display account information"""
    info = AccountInfoQuery(account_id).execute(client)

    print(f"Account ID: {info.account_id}")
    print(f"Account Balance: {info.balance}")
    print(f"Account Memo: '{info.account_memo}'")
    print(f"Public Key: {info.key}")
    print(f"Receiver Signature Required: {info.receiver_signature_required}")
    print(f"Expiration Time: {info.expiration_time}")
    print(f"Auto Renew Period: {info.auto_renew_period}")


def account_update():
    """
    Demonstrates account update functionality by:
    1. Setting up client with operator account
    2. Creating a test account
    3. Querying the account info
    4. Updating the account properties
    5. Querying the account info again
    """
    client = setup_client()

    # Create a test account first
    account_id, account_private_key = create_account(client)

    print("\nAccount info before update:")
    # Query the account info
    query_account_info(client, account_id)

    # Generate a new private key for key rotation
    new_private_key = PrivateKey.generate_ed25519()
    new_public_key = new_private_key.public_key()

    # Create a future expiration time (92 days from now)
    current_time = datetime.datetime.now(datetime.timezone.utc)
    future_expiration = Timestamp.from_date(current_time + datetime.timedelta(days=92))
    print(f"\nFuture expiration time: {future_expiration}")

    # Update the account
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_key(new_public_key)
        .set_account_memo("Updated account memo!")
        .set_receiver_signature_required(True)
        .set_auto_renew_period(Duration(6912000))  # ~80 days
        .set_expiration_time(future_expiration)
        .freeze_with(client)
        .sign(account_private_key)  # Sign with old key
        .sign(new_private_key)  # Sign with new key
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account update failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("\nAccount info after update:")
    # Query the account info again
    query_account_info(client, account_id)


if __name__ == "__main__":
    account_update()
