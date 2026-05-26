"""
Example demonstrating high-volume account creation functionality.

Run:
uv run examples/account/high_volume_account_create_transaction.py
python examples/account/high_volume_account_create_transaction.py
"""

import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountDeleteTransaction,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
)


def create_account_high_volume(client):
    """Create a test account using high-volume throttles."""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("High-volume test account")
        .set_high_volume(True)
        .set_max_transaction_fee(Hbar(5))
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


def main():
    """
    Demonstrates high-volume account creation functionality by:

    1. Setting up client with operator account
    2. Creating an account using high-volume throttles
    3. Setting a max transaction fee for dynamic pricing protection
    4. Deleting the created account
    """
    load_dotenv()
    client = Client.from_env()

    # Create an account using high-volume throttles
    account_id, account_private_key = create_account_high_volume(client)

    print("Account created successfully using high-volume throttles!")

    # Delete the account
    receipt = (
        AccountDeleteTransaction()
        .set_account_id(account_id)
        .set_transfer_account_id(client.operator_account_id)
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account delete failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Account deleted successfully!")


if __name__ == "__main__":
    main()
