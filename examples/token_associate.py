import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
    AccountCreateTransaction,
    TokenCreateTransaction,
    TokenAssociateTransaction,
)

# Load environment variables from .env file
load_dotenv()


def create_and_associate_token():
    """
    A full example that creates an account, creates a token,
    and associates the token with the new account.
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

    # 2. Create a new account to associate the token with
    # =================================================================
    print("\nSTEP 1: Creating a new account...")
    recipient_key = PrivateKey.generate_ed25519()
    recipient_public_key = recipient_key.public_key()

    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_public_key)
            .set_initial_balance(Hbar.from_tinybars(100_000_000)) # 1 Hbar
        )
        receipt = tx.execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created new account with ID: {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating new account: {e}")
        sys.exit(1)


    # 3. Create a new token
    # =================================================================
    print("\nSTEP 2: Creating a new fungible token...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("My Associable Token")
            .set_token_symbol("MAT")
            .set_initial_supply(1_000_000)
            .set_treasury_account_id(operator_id)
        )
        receipt = tx.execute(client)
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

    # 4. Associate the token with the new account
    # =================================================================
    print(f"\nSTEP 3: Associating token {token_id} with account {recipient_id}...")
    try:
        # Note: The operator pays for this transaction, but the recipient must sign it.
        tx = (
            TokenAssociateTransaction()
            .set_account_id(recipient_id)
            .add_token_id(token_id)
            .freeze_with(client)  # Freeze against the client (operator)
            .sign(recipient_key)  # The recipient *must* sign to approve the association
        )
        receipt = tx.execute(client)
        print(f"✅ Success! Token association complete.")
    except Exception as e:
        print(f"❌ Error associating token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_and_associate_token()