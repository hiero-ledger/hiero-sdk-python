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
)

# Load environment variables from .env file
load_dotenv()


def token_unfreeze():
    """
    Creates a freezeable token, freezes it for the treasury account,
    and then unfreezes it.
    """
    # 1. Setup Client
    # =================================================================
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

    print(f"Using operator account: {operator_id}")

    # 2. Generate a Freeze Key on the fly
    # =================================================================
    print("\nSTEP 1: Generating a new freeze key...")
    freeze_key = PrivateKey.generate("ed25519")
    print("✅ Freeze key generated.")

    # 3. Create a token with the freeze key
    # =================================================================
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
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(freeze_key)
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

    # 4. Freeze the token for the operator account
    # =================================================================
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
        print(f"✅ Success! Token freeze complete.")
    except Exception as e:
        print(f"❌ Error freezing token: {e}")
        sys.exit(1)

    # 5. Unfreeze the token for the operator account
    # =================================================================
    print(f"\nSTEP 4: Unfreezing token {token_id} for operator account {operator_id}...")
    try:
        receipt = (
            TokenUnfreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id)
            .freeze_with(client)
            .sign(freeze_key)
            .execute(client)
        )
        print(f"✅ Success! Token unfreeze complete.")
    except Exception as e:
        print(f"❌ Error unfreezing token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_unfreeze()