"""
Creates a freezeable token, freezes it for the treasury account,
and then unfreezes it.
uv run examples/tokens/token_unfreeze_transaction.py
python examples/tokens/token_unfreeze_transaction.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TokenCreateTransaction,
    TokenFreezeTransaction,
    TokenUnfreezeTransaction,
    TransferTransaction,
    ResponseCode,
)

# Load environment variables from .env file
load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Setup Client"""
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
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_freeze_key():
    """Generate a Freeze Key on the fly"""
    print("\nSTEP 1: Generating a new freeze key...")
    freeze_key = PrivateKey.generate(os.getenv("KEY_TYPE", "ed25519"))
    print("✅ Freeze key generated.")
    return freeze_key


def create_freezable_token():
    """Create a token with the freeze key"""
    client, operator_id, operator_key = setup_client()
    freeze_key = generate_freeze_key()
    print("\nSTEP 2: Creating a new freezeable token...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("Unfreezeable Token")
            .set_token_symbol("UFT")
            .set_initial_supply(1000)
            .set_treasury_account_id(operator_id)
            .set_freeze_key(freeze_key)
        )

        # FIX: The .execute() method returns the receipt directly.
        receipt = (
            tx.freeze_with(client).sign(operator_key).sign(freeze_key).execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
        return token_id, client, operator_id, freeze_key, operator_key
    except (RuntimeError, ValueError) as e:
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
            f"✅ Success! Token freeze complete, Status: {ResponseCode(receipt.status).name}"
        )
    except (RuntimeError, ValueError) as e:
        print(f"❌ Error freezing token: {e}")
        sys.exit(1)


def unfreeze_token(token_id, client, operator_id, freeze_key, operator_key):
    """Unfreeze the token for the operator account"""
    # Step 1: Unfreeze the token for the operator account
    print(
        f"\nSTEP 4: Unfreezing token {token_id} for operator account {operator_id}..."
    )
    try:
        receipt = (
            TokenUnfreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id)
            .freeze_with(client)
            .sign(freeze_key)
            .execute(client)
        )
        print(
            f"✅ Success! Token unfreeze complete, Status: {ResponseCode(receipt.status).name}"
        )

        # Step 2: Attempt a test transfer of 1 unit of token to self
        print(f"Attempting a test transfer of 1 unit of token {token_id} to self...")
        try:
            transfer_receipt = (
                TransferTransaction()
                .add_token_transfer(token_id, operator_id, 1)
                .add_token_transfer(token_id, operator_id, -1)
                .freeze_with(client)
                .sign(operator_key)
                .execute(client)
            )
            print(
                f"✅ Test transfer succeeded. Token is unfrozen and usable, Status: {ResponseCode(transfer_receipt.status).name}"
            )
        except (RuntimeError, ValueError) as transfer_error:
            print(f"❌ Test transfer failed: {transfer_error}")
    except (RuntimeError, ValueError) as e:
        print(f"❌ Error unfreezing token: {e}")
        sys.exit(1)


def main():
    """Unfreeze the token for the operator account.
    1. Freeze the token for the operator account (calls freeze_token()).
    2. Unfreeze the token for the operator account using TokenUnfreezeTransaction.
    3. Attempt a test transfer of 1 unit of the token to self to verify unfreeze.
    """
    token_id, client, operator_id, freeze_key, operator_key = create_freezable_token()
    freeze_token(token_id, client, operator_id, freeze_key)
    unfreeze_token(token_id, client, operator_id, freeze_key, operator_key)


if __name__ == "__main__":
    main()
