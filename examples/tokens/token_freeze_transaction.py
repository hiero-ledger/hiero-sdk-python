"""
Creates a freezeable token and demonstrates freezing and unfreezing
the token for the operator (treasury) account.

uv run examples/tokens/token_freeze_transaction.py
python examples/tokens/token_freeze_transaction.py
"""

import os
import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenFreezeTransaction,
    TransferTransaction,
    ResponseCode,
)


def setup_client():
    """Setup client from environment variables"""
    client = Client.from_env()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {operator_id}")

    return client, operator_id, operator_key


def generate_freeze_key():
    """Generate a Freeze Key"""
    print("\nSTEP 1: Generating a new freeze key...")
    freeze_key = PrivateKey.generate(os.getenv("KEY_TYPE", "ed25519"))
    print("✅ Freeze key generated.")
    return freeze_key


def create_freezeable_token(client, operator_id, operator_key):
    """Create a token with the freeze key"""
    freeze_key = generate_freeze_key()
    print("\nSTEP 2: Creating a new freezeable token...")

    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("Freezeable Token")
            .set_token_symbol("FRZ")
            .set_initial_supply(1000)
            .set_treasury_account_id(operator_id)
            .set_freeze_key(freeze_key)
        )

        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(freeze_key)
            .execute(client)
        )

        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")

        return freeze_key, token_id, client, operator_id, operator_key

    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def freeze_token(token_id, client, operator_id, freeze_key):
    """Freeze the token for the operator account"""
    print(f"\nSTEP 3: Freezing token {token_id} for operator account {operator_id}...")

    try:
        receipt = (
            TokenFreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id)
            .freeze_with(client)
            .sign(freeze_key)
            .execute(client)
        )

        print(
            f"✅ Success! Token freeze complete. Status: {ResponseCode(receipt.status).name}"
        )

    except Exception as e:
        print(f"❌ Error freezing token: {e}")
        sys.exit(1)


def verify_freeze(token_id, client, operator_id, operator_key):
    """Attempt a token transfer to confirm the account is frozen"""
    print("\nVerifying freeze: Attempting token transfer...")

    try:
        transfer_receipt = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, 1)
            .add_token_transfer(token_id, operator_id, -1)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        status_name = ResponseCode(transfer_receipt.status).name

        if status_name in ["ACCOUNT_FROZEN_FOR_TOKEN", "ACCOUNT_FROZEN"]:
            print(
                f"✅ Verified: Transfer blocked as expected due to freeze. Status: {status_name}"
            )
        elif status_name == "SUCCESS":
            print(
                "❌ Error: Transfer succeeded, but should have failed because the account is frozen."
            )
        else:
            print(f"❌ Unexpected transfer result. Status: {status_name}")

    except Exception as e:
        print(f"❌ Error during transfer verification: {e}")
        sys.exit(1)


def main():
    """
    1. Create a freezeable token with a freeze key.
    2. Freeze the token for the operator account using the freeze key.
    3. Attempt a token transfer to verify the freeze (should fail).
    """
    client, operator_id, operator_key = setup_client()

    freeze_key, token_id, client, operator_id, operator_key = create_freezeable_token(
        client, operator_id, operator_key
    )

    freeze_token(token_id, client, operator_id, freeze_key)
    verify_freeze(token_id, client, operator_id, operator_key)


if __name__ == "__main__":
    main()
