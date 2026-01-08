# uv run examples/tokens/token_delete_transaction.py
# python examples/tokens/token_delete_transaction.py

import os
import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenDeleteTransaction,
    ResponseCode,
)



def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def generate_admin_key():
    """Generate a new admin key within the script:
    This key will be used to create the token with admin privileges
    """

    print("\nGenerating a new admin key for the token...")
    admin_key = PrivateKey.generate(os.getenv("KEY_TYPE", "ed25519"))
    print("Admin key generated successfully.")
    return admin_key


def create_new_token(client, admin_key):
    """Create the Token"""
    token_id_to_delete = None

    try:
        print("\nSTEP 1: Creating a new token...")
        create_tx = (
            TokenCreateTransaction()
            .set_token_name("My Deletable Token")
            .set_token_symbol("MDT")
            .set_initial_supply(1)  # <-- ADD THIS LINE
            .set_treasury_account_id(client.operator_account_id)
            .set_admin_key(admin_key)  # Use the newly generated admin key
            .freeze_with(client)
            .sign(client.operator_private_key)  # Operator (treasury) must sign
            .sign(admin_key)  # The new admin key must also sign
        )

        create_receipt = create_tx.execute(client)

        # Verify the receipt status
        rc = ResponseCode(create_receipt.status)
        if rc != ResponseCode.SUCCESS:
            print(f"❌ Token creation failed with status: {rc.name}")
            sys.exit(1)

        token_id_to_delete = create_receipt.token_id
        print(f"✅ Token created successfully: {token_id_to_delete}")
        return token_id_to_delete

    except Exception as e:
        print(f"❌ Error creating token: {repr(e)}")
        sys.exit(1)


def delete_token(admin_key, token_id_to_delete, client):
    """
    Delete the Token we just created
    """

    try:
        print(f"\nSTEP 2: Deleting token {token_id_to_delete}...")
        delete_tx = (
            TokenDeleteTransaction()
            .set_token_id(token_id_to_delete)  # Use the ID from the token we just made
            .freeze_with(client)  # Use the ID from the token we just made
            .sign(client.operator_private_key)  # Operator must sign
            .sign(admin_key)  # Sign with the same admin key used to create it
        )

        delete_receipt = delete_tx.execute(client)

        # Verify deletion receipt status
        rc = ResponseCode(delete_receipt.status)
        if rc != ResponseCode.SUCCESS:
            print(f"❌ Token deletion failed with status: {rc.name}")
            sys.exit(1)

        print(f"✅ Token {token_id_to_delete} deleted successfully!")

    except Exception as e:
        print(f"❌ Error deleting token: {repr(e)}")
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
    client = setup_client()
    admin_key = generate_admin_key()
    token_id_to_delete = create_new_token(client, admin_key)
    delete_token(admin_key, token_id_to_delete, client)


if __name__ == "__main__":
    main()
