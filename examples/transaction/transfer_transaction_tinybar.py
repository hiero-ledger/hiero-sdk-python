"""Example of transferring tinybars using legacy integer and modern Hbar object approaches.

Usage:
    uv run examples/transaction/transfer_transaction_tinybar.py
    python examples/transaction/transfer_transaction_tinybar.py
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

TINYBARS_TO_TRANSFER = 100_000_000


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


def transfer_hbar_with_integer(client, operator_id, recipient_id, operator_key):
    """Demonstrate legacy approach using raw integers (tinybars)."""
    print("\nSTEP 2: Transferring using Integers (Legacy Approach)...")

    try:
        receipt = (
            TransferTransaction()
            .add_hbar_transfer(operator_id, -TINYBARS_TO_TRANSFER)
            .add_hbar_transfer(recipient_id, TINYBARS_TO_TRANSFER)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if receipt.status == ResponseCode.SUCCESS:
            print(f"✅ Success! Transferred {TINYBARS_TO_TRANSFER} tinybars (Integer).")
        else:
            print(f"❌ Failed with status: {receipt.status}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Transfer failed: {str(e)}")
        sys.exit(1)


def transfer_hbar_with_object(client, operator_id, recipient_id, operator_key):
    """Demonstrate modern approach using Hbar objects with Tinybar units."""
    print("\nSTEP 3: Transferring using Hbar Objects (Tinybar Unit)...")

    amount = Hbar.from_tinybars(TINYBARS_TO_TRANSFER)

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
            print(f"✅ Success! Transferred {amount} (Object).")
        else:
            print(f"❌ Failed with status: {receipt.status}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Transfer failed: {str(e)}")
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
    """Run example showing both integer and object-based tinybar transfers.

    Steps:
    1. Setup client.
    2. Create recipient account.
    3. Transfer using legacy integer method (tinybars).
    4. Transfer using modern Hbar object method.
    """
    client, operator_id, operator_key = setup_client()

    recipient_id, _ = create_account(client, operator_key)

    # Legacy Approach
    transfer_hbar_with_integer(client, operator_id, recipient_id, operator_key)
    get_balance(client, recipient_id, " after integer")

    # Modern Approach
    transfer_hbar_with_object(client, operator_id, recipient_id, operator_key)
    get_balance(client, recipient_id, " after object")

    print("\n🎉 Example Finished Successfully!")


if __name__ == "__main__":
    main()
