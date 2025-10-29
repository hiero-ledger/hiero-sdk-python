"""
Query Balance Example

This script demonstrates how to:
1. Set up a client connection to the Hedera network
2. Create a new account with an initial balance
3. Query account balance
4. Transfer HBAR between accounts

Run with:
  uv run examples/query_balance.py
  python examples/query_balance.py

"""
import os
import sys
import time
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    TransferTransaction,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
)

load_dotenv()


def setup_client():
    """
    Initialize and configure the Hiero SDK client with operator credentials.

    Returns:
        Client: Configured client ready for transactions and queries.

    Raises:
        ValueError: If OPERATOR_ID or OPERATOR_KEY environment variables are not set.
    """
    print("Setting up client connection...")
    network = Network(os.getenv('NETWORK'))
    client = Client(network)

    operator_id_str = os.getenv('OPERATOR_ID')
    operator_key_str = os.getenv('OPERATOR_KEY')

    if not operator_id_str or not operator_key_str:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY environment variables must be set")

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    client.set_operator(operator_id, operator_key)

    print(f"✓ Client configured with operator: {operator_id}\n")
    return client, operator_id, operator_key


def create_account(client, operator_key, initial_balance=Hbar(10)):
    """
    Create a new account on the Hedera network with an initial balance.

    Args:
        client (Client): The Hiero SDK client.
        operator_key (PrivateKey): The operator's private key for signing transactions.
        initial_balance (Hbar): Initial HBAR balance for the new account. Defaults to 10 HBAR.

    Returns:
        tuple: (new_account_id, new_account_private_key) - The ID and private key of the new account.
    """
    print("Creating new account...")

    # Generate new account's cryptographic keys
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    # Create the account creation transaction
    transaction = AccountCreateTransaction(
        key=new_account_public_key,
        initial_balance=initial_balance,
        memo="New Account"
    ).freeze_with(client)

    # Sign and execute the transaction
    transaction.sign(operator_key)
    receipt = transaction.execute(client)
    new_account_id = receipt.account_id

    print(f"✓ Account created successfully")
    print(f"  Account ID: {new_account_id}")
    print(
        f"  Initial balance: {initial_balance.to_hbars()} hbars ({initial_balance.to_tinybars()} tinybars)\n")

    return new_account_id, new_account_private_key


def get_balance(client, account_id):
    """
    Query and retrieve the HBAR balance of an account.

    Args:
        client (Client): The Hiero SDK client.
        account_id (AccountId): The account ID to query.

    Returns:
        Hbar: The account's current balance in HBAR.
    """
    print(f"Querying balance for account {account_id}...")

    balance_query = CryptoGetAccountBalanceQuery().set_account_id(account_id)
    balance = balance_query.execute(client)

    balance_hbar = balance.hbars.to_hbars()
    print(f"✓ Balance retrieved: {balance_hbar} hbars\n")
    return balance_hbar


def transfer_hbars(client, operator_id, operator_key, recipient_id, amount):
    """
    Transfer HBAR from the operator account to a recipient account.

    Args:
        client (Client): The Hiero SDK client.
        operator_id (AccountId): The sender's (operator's) account ID.
        operator_key (PrivateKey): The operator's private key for signing.
        recipient_id (AccountId): The recipient's account ID.
        amount (Hbar): The amount of HBAR to transfer.

    Returns:
        str: The status of the transfer transaction.
    """
    print(
        f"Transferring {amount.to_tinybars()} tinybars ({amount.to_hbars()} hbars) from {operator_id} to {recipient_id}...")

    # Create transfer transaction
    transfer_transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -amount.to_tinybars())
        .add_hbar_transfer(recipient_id, amount.to_tinybars())
        .freeze_with(client)
    )

    # Sign and execute the transaction
    transfer_transaction.sign(operator_key)
    transfer_receipt = transfer_transaction.execute(client)

    status = ResponseCode(transfer_receipt.status).name
    print(f"✓ Transfer completed with status: {status}\n")

    return status


def main():
    """
    Main workflow: Set up client, create account, query balance, and transfer HBAR.
    """
    try:
        #  Initialize client with operator credentials
        client, operator_id, operator_key = setup_client()

        #  Create a new account with initial balance
        new_account_id, new_account_private_key = create_account(
            client, operator_key, initial_balance=Hbar(10))

        #  Query and display the initial balance
        print("=" * 60)
        print("INITIAL BALANCE CHECK")
        print("=" * 60)
        initial_balance = get_balance(client, new_account_id)
        print(f"Initial balance of new account: {initial_balance} hbars")
        print("=" * 60 + "\n")

        # Transfer additional HBAR to the new account
        print("=" * 60)
        print("EXECUTING TRANSFER")
        print("=" * 60)
        transfer_amount = Hbar(5)
        transfer_status = transfer_hbars(
            client, operator_id, operator_key, new_account_id, transfer_amount)
        print(f"Transfer transaction status: {transfer_status}")
        print("=" * 60 + "\n")

        # Wait briefly for the transaction to be fully processed
        print("Waiting for transfer to be processed...")
        time.sleep(2)

        #  Query and display the updated balance
        print("=" * 60)
        print("UPDATED BALANCE CHECK")
        print("=" * 60)
        updated_balance = get_balance(client, new_account_id)
        print(f"Updated balance of new account: {updated_balance} hbars")
        print("=" * 60 + "\n")

        print("✓ All operations completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
