"""Example of transferring HBAR using the GIGABAR unit.

Usage:
    uv run examples/transaction/transfer_transaction_gigabar.py
    python examples/transaction/transfer_transaction_gigabar.py
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
    HbarUnit,
    Network,
    PrivateKey,
    ResponseCode,
    TransferTransaction,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()

# 0.00000001 Gigabars = 10 Hbar
GIGABARS_TO_TRANSFER = 0.00000001


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
        tx = AccountCreateTransaction().set_key(recipient_key.public_key()).set_initial_balance(Hbar.from_tinybars(0))

        receipt = tx.freeze_with(client).sign(operator_key).execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(f"❌ Account creation failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        recipient_id = receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
        return recipient_id, recipient_key

    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def transfer_gigabars(client, operator_id, recipient_id, operator_key):
    """Transfer HBAR using the GIGABAR unit."""
    print(f"\nSTEP 2: Transferring {GIGABARS_TO_TRANSFER} GIGABARS...")
    print("(Note: 1 Gigabar = 1,000,000,000 Hbar)")

    amount = Hbar.of(GIGABARS_TO_TRANSFER, HbarUnit.GIGABAR)

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
            print(f"✅ Success! Transferred {amount} successfully.")
        else:
            print(f"❌ Failed with status: {receipt.status}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Transfer failed: {str(e)}")
        sys.exit(1)


def get_balance(client, account_id, when=""):
    """Query and display account balance."""
    try:
        balance = CryptoGetAccountBalanceQuery(account_id=account_id).execute(client).hbars
        print(f"Recipient account balance{when}: {balance} hbars")
        return balance
    except Exception as e:
        print(f"❌ Balance query failed: {str(e)}")
        sys.exit(1)


def main():
    """Run example demonstrating large-value transfers using GIGABAR units.

    Steps:
    1. Setup client.
    2. Create recipient account (0 balance).
    3. Transfer Gigabars using Hbar unit.
    4. Verify balance.
    """
    client, operator_id, operator_key = setup_client()
    recipient_id, _ = create_account(client, operator_key)

    transfer_gigabars(client, operator_id, recipient_id, operator_key)
    get_balance(client, recipient_id, " after transfer")

    print("\n🎉 Example Finished Successfully!")


if __name__ == "__main__":
    main()
