"""
Example demonstrating account delete functionality.
Run:
uv run examples/account/account_delete_transaction.py
python examples/account/account_delete_transaction.py

"""

import sys
from hiero_sdk_python import (
    Client,
    Hbar,
    PrivateKey,
    AccountCreateTransaction,
    AccountDeleteTransaction,
    ResponseCode,
)


def create_account(client):
    """Create a test account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Test account for delete")
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


def account_delete():
    """
    Demonstrates account delete functionality by:
    1. Setting up client with operator account
    2. Creating an account
    3. Deleting the account
    """
    client = Client.from_env()

    # Create an account first
    account_id, account_private_key = create_account(client)

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
    account_delete()
