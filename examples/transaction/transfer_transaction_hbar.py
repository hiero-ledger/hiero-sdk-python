"""Example of transferring HBAR using the Hiero Python SDK.

Usage:
    uv run examples/transaction/transfer_transaction_hbar.py
    python examples/transaction/transfer_transaction_hbar.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    CryptoGetAccountBalanceQuery,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
    TransferTransaction,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()

HBAR_TO_TRANSFER = 1


def setup_client():
    """Initialize and set up the client with operator account."""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)


def create_account(client, operator_key):
    """Create a new recipient account."""
    print("\nSTEP 1: Creating a new recipient account...")
    recipient_key = PrivateKey.generate()
    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Account creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        recipient_id = receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
        return recipient_id, recipient_key

    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def transfer_hbar(client, operator_id, recipient_id, operator_key):
    """Transfer HBAR from operator account to recipient account."""
    print("\nSTEP 2: Transferring HBAR...")

    amount = Hbar(HBAR_TO_TRANSFER)  # HBAR object

    try:
        receipt = (
            TransferTransaction()
            .add_hbar_transfer(operator_id, amount.negated())
            .add_hbar_transfer(recipient_id, amount)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if receipt.status == ResponseCode.SUCCESS:
            print(f"\n✅ Success! Transferred {amount} to {recipient_id}.")
            print(f"Transaction ID: {receipt.transaction_id}\n")
        else:
            print(f"\n❌ Unexpected status: {receipt.status}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ HBAR transfer failed: {str(e)}")
        sys.exit(1)


def get_balance(client, account_id, when=""):
    """Query and display account balance."""
    try:
        balance = (
            CryptoGetAccountBalanceQuery(account_id=account_id).execute(client).hbars
        )
        print(f"Recipient account balance{when}: {balance} hbars")
        return balance
    except Exception as e:
        print(f"❌ Balance query failed: {str(e)}")
        sys.exit(1)


def main():
    """Run a full example to create a new recipient account and transfer hbar to that account.

    Steps:
    1. Setup client with operator credentials.
    2. Create a new account with initial balance.
    3. Transfer HBAR from operator to new account.
    4. Verify balance updates.
    """
    client, operator_id, operator_key = setup_client()

    recipient_id, _ = create_account(client, operator_key)

    get_balance(client, recipient_id, " before transfer")

    transfer_hbar(client, operator_id, recipient_id, operator_key)

    get_balance(client, recipient_id, " after transfer")


if __name__ == "__main__":
    main()
