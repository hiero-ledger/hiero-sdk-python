"""
Example demonstrating account update functionality with key lists (multi-signature threshold keys).

run with:
uv run examples/account/account_update_transaction_with_keylist.py
python examples/account/account_update_transaction_with_keylist.py

"""

import sys

from hiero_sdk_python import Client, Hbar, PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode


def setup_client() -> Client:
    """Setup Client."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_account(client):
    """Create a test account."""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Test account for update with keylist")
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


def query_account_info(client, account_id):
    """Query and display account information."""
    info = AccountInfoQuery(account_id).execute(client)

    print(f"Account ID: {info.account_id}")
    print(f"Account Balance: {info.balance}")
    print(f"Account Memo: '{info.account_memo}'")
    print(f"Public Key: {info.key}")


def account_update_with_keylist():
    """
    Demonstrates account update functionality using a threshold key list by:

    1. Setting up client with operator account
    2. Creating a test account
    3. Updating the account to use a KeyList with threshold
    4. Proving that the new account key is active by signing an update
    """
    client = setup_client()

    # Create a test account first
    account_id, current_private_key = create_account(client)

    print("\nAccount info before update:")
    # Query the account info
    query_account_info(client, account_id)

    # Rotate from a single key to a threshold KeyList (2 of 2).
    threshold_key_1 = PrivateKey.generate_ed25519()
    threshold_key_2 = PrivateKey.generate_ed25519()
    threshold_key = KeyList([threshold_key_1.public_key(), threshold_key_2.public_key()], threshold=2)

    print("\nRotating account key to a 2-of-2 threshold KeyList...")
    key_list_receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_key(threshold_key)
        .freeze_with(client)
        .sign(current_private_key)  # Sign with current key
        .sign(threshold_key_1)  # First signature for threshold=2
        .sign(threshold_key_2)  # Second signature for threshold=2
        .execute(client)
    )

    if key_list_receipt.status != ResponseCode.SUCCESS:
        print(f"KeyList rotation failed with status: {ResponseCode(key_list_receipt.status).name}")
        sys.exit(1)

    print("\nAccount info after KeyList update:")
    query_account_info(client, account_id)

    # Prove the new account key is active by signing with both threshold keys.
    print("\nProving the new account key by updating the memo using both threshold keys...")
    memo_receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_account_memo("Updated account memo with threshold key")
        .freeze_with(client)
        .sign(threshold_key_1)
        .sign(threshold_key_2)
        .execute(client)
    )

    if memo_receipt.status != ResponseCode.SUCCESS:
        print(f"Memo update with threshold key failed with status: {ResponseCode(memo_receipt.status).name}")
        sys.exit(1)

    print("\nAccount info after memo update:")
    query_account_info(client, account_id)

    print("\nThreshold KeyList rotation and follow-up update succeeded.")


if __name__ == "__main__":
    account_update_with_keylist()
