"""
Query Balance Example

This script demonstrates how to:
1. Set up a client connection to the Hedera network
2. Create a new account with an initial balance
3. Query account balance
4. Transfer HBAR between accounts

Run with:
  uv run examples/query/account_balance_query.py
  python examples/query/account_balance_query.py
"""

import sys
import time

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    TransferTransaction,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
)


def setup_client():
    """
    Initialize and configure the Hiero SDK client using environment variables.

    Returns:
        tuple: (Client, operator_id, operator_key)
    """
    print("Connecting to Hedera network using environment configuration...")

    client = Client.from_env()

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    if not operator_id or not operator_key:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY must be set in the environment"
        )

    print(f"Client set up with operator id {operator_id}")
    return client, operator_id, operator_key


def create_account(client, operator_key, initial_balance=Hbar(10)):
    """
    Create a new account on the Hedera network with an initial balance.
    """
    print("Creating new account...")

    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(new_account_public_key)
        .set_initial_balance(initial_balance)
        .freeze_with(client)
    )

    transaction.sign(operator_key)
    receipt = transaction.execute(client)

    new_account_id = receipt.account_id

    print("✓ Account created successfully")
    print(f"  Account ID: {new_account_id}")
    print(
        f"  Initial balance: {initial_balance.to_hbars()} hbars "
        f"({initial_balance.to_tinybars()} tinybars)\n"
    )

    return new_account_id, new_account_private_key


def get_balance(client, account_id):
    """
    Query and retrieve the HBAR balance of an account.
    """
    print(f"Querying balance for account {account_id}...")

    balance = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(account_id)
        .execute(client)
    )

    balance_hbar = balance.hbars.to_hbars()
    print(f"✓ Balance retrieved: {balance_hbar} hbars\n")
    return balance_hbar


def transfer_hbars(client, operator_id, operator_key, recipient_id, amount):
    """
    Transfer HBAR from the operator account to a recipient account.
    """
    print(
        f"Transferring {amount.to_hbars()} hbars from "
        f"{operator_id} to {recipient_id}..."
    )

    transfer_transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -amount.to_tinybars())
        .add_hbar_transfer(recipient_id, amount.to_tinybars())
        .freeze_with(client)
    )

    transfer_transaction.sign(operator_key)
    receipt = transfer_transaction.execute(client)

    status = ResponseCode(receipt.status).name
    print(f"✓ Transfer completed with status: {status}\n")

    return status


def main():
    """
    Main workflow: Set up client, create account, query balance, and transfer HBAR.
    """
    try:
        client, operator_id, operator_key = setup_client()

        new_account_id, _ = create_account(
            client, operator_key, initial_balance=Hbar(10)
        )

        print("=" * 60)
        print("INITIAL BALANCE CHECK")
        print("=" * 60)
        get_balance(client, new_account_id)

        print("=" * 60)
        print("EXECUTING TRANSFER")
        print("=" * 60)
        transfer_hbars(
            client,
            operator_id,
            operator_key,
            new_account_id,
            Hbar(5),
        )

        print("Waiting for transfer to be processed...")
        time.sleep(2)

        print("=" * 60)
        print("UPDATED BALANCE CHECK")
        print("=" * 60)
        get_balance(client, new_account_id)

        print("✓ All operations completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
