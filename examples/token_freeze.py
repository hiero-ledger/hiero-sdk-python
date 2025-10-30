"""
uv run examples/token_freeze.py
python examples/token_freeze.py

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
)

# Load environment variables from .env file
load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()

def freeze_token():
    """
    Creates a freezeable token and demonstrates freezing and unfreezing
    the token for the operator (treasury) account.
    """
    # 1. Setup Client
    # =================================================================
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

    print(f"Using operator account: {operator_id}")

    # 2. Generate a Freeze Key
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
            .set_token_name("Freezeable Token")
            .set_token_symbol("FRZ")
            .set_initial_supply(1000)
            .set_treasury_account_id(operator_id)
            .set_freeze_key(freeze_key) # <-- THE FIX: Pass the private key directly
        )
        
        # Freeze, sign with BOTH operator and the new freeze key, then execute
        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(freeze_key) # The new freeze key must sign to give consent
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
            .set_account_id(operator_id) # Target the operator account
            .freeze_with(client)
            .sign(freeze_key) # Must be signed by the freeze key
            .execute(client)
        )
        print(f"✅ Success! Token freeze complete. Status: {receipt.status}")
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
            .set_account_id(operator_id) # Target the operator account
            .freeze_with(client)
            .sign(freeze_key) # Also signed by the freeze key
            .execute(client)
        )
        print(f"✅ Success! Token unfreeze complete. Status: {receipt.status}")
    except Exception as e:
        print(f"❌ Error unfreezing token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    freeze_token()