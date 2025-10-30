"""
uv run examples/token_delete.py
python examples/token_delete.py

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
    TokenDeleteTransaction,
)

# Load environment variables from .env file
load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()

def create_and_delete_token():
    """
    A full example that creates a token and then immediately deletes it.
    """
    # 1. Setup Client
    # =================================================================
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))

    # Get the operator account from the .env file
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        # NOTE: Assumes your operator key is a raw Ed25519 key
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)
    print(f"Using operator account: {operator_id}")

    # 2. Generate a new admin key within the script
    # =================================================================
    print("\nGenerating a new admin key for the token...")
    admin_key = PrivateKey.generate_ed25519()
    print("Admin key generated successfully.")
    token_id_to_delete = None

    # 3. Create the Token
    # =================================================================
    try:
        print("\nSTEP 1: Creating a new token...")
        create_tx = (
            TokenCreateTransaction()
            .set_token_name("My Deletable Token")
            .set_token_symbol("MDT")
            .set_initial_supply(1)  # <-- ADD THIS LINE
            .set_treasury_account_id(operator_id)
            .set_admin_key(admin_key)  # Use the newly generated admin key
            .freeze_with(client)
            .sign(operator_key)  # Operator (treasury) must sign
            .sign(admin_key)     # The new admin key must also sign
        )

        create_receipt = create_tx.execute(client)
        token_id_to_delete = create_receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id_to_delete}")

    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


    # 4. Delete the Token
    # =================================================================
    try:
        print(f"\nSTEP 2: Deleting token {token_id_to_delete}...")
        delete_tx = (
            TokenDeleteTransaction()
            .set_token_id(token_id_to_delete)  # Use the ID from the token we just made
            .freeze_with(client)
            .sign(operator_key)  # Operator must sign
            .sign(admin_key)     # Sign with the same admin key used to create it
        )

        delete_receipt = delete_tx.execute(client)
        print(f"✅ Success! Token deleted.")

    except Exception as e:
        print(f"❌ Error deleting token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_and_delete_token()