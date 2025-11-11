# uv run examples/token_delete.py
# python examples/token_delete.py
"""
A full example that creates a token and then immediately deletes it.
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

def setup_client():
    """Setup Client """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # Get the operator account from the .env file
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        # Set the operator (payer) account for the client
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)
    

def generate_admin_key():
    """Generate a new admin key within the script:
    This key will be used to create the token with admin privileges
    """

    print("\nGenerating a new admin key for the token...")
    admin_key = PrivateKey.generate(os.getenv('KEY_TYPE', 'ed25519'))
    print("Admin key generated successfully.")
    return admin_key

def create_new_token(client, operator_id, operator_key, admin_key):
    """ Create the Token"""
    token_id_to_delete = None

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
        return token_id_to_delete

    except (ValueError, TypeError) as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def delete_token(admin_key, token_id_to_delete, client, operator_key):
    """
    Delete the Token we just created
    """

    try:
        print(f"\nSTEP 2: Deleting token {token_id_to_delete}...")
        delete_tx = (
            TokenDeleteTransaction()
            .set_token_id(token_id_to_delete)  # Use the ID from the token we just made
            .freeze_with(client)
            .sign(operator_key)  # Operator must sign
            .sign(admin_key)     # Sign with the same admin key used to create it
        )

        delete_tx.execute(client)
        print("✅ Success! Token deleted.")

    except (ValueError, TypeError) as e:
        print(f"❌ Error deleting token: {e}")
        sys.exit(1)

def main():
    """
    1. Call create_new_token() to create a new token and get its admin key, token ID, client, and operator key.
    2. Build a TokenDeleteTransaction using the token ID.
    3. Freeze the transaction with the client.
    4. Sign the transaction with both the operator key and the admin key.
    5. Execute the transaction to delete the token.
    6. Print the result or handle any errors.
    """
    client, operator_id, operator_key = setup_client()
    admin_key = generate_admin_key()
    token_id_to_delete = create_new_token(client, operator_id, operator_key, admin_key)
    delete_token(admin_key, token_id_to_delete, client, operator_key)

if __name__ == "__main__":
    main()
