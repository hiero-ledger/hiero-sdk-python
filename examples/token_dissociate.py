"""
uv run examples/token_dissociate.py
python examples/token_dissociate.py

"""
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
    TokenDissociateTransaction,
)

# Load environment variables from .env file
load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()
def token_dissociate():
    """
    A full example that creates an account, two tokens, associates them,
    and finally dissociates them.
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

    # 2. Create a new account to associate/dissociate with
    # =================================================================
    print("\nSTEP 1: Creating a new account...")
    recipient_key = PrivateKey.generate("ed25519")
    try:
        # Build the transaction
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key()) # <-- THE FIX: Call as a method
            .set_initial_balance(Hbar.from_tinybars(100_000_000)) # 1 Hbar
        )

        # Freeze the transaction, sign with the operator, then execute
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created new account with ID: {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating new account: {e}")
        sys.exit(1)

    # 3. Create two new tokens
    # =================================================================
    print("\nSTEP 2: Creating two new tokens...")
    try:
        # Create First Token
        tx1 = TokenCreateTransaction().set_token_name("First Token").set_token_symbol("TKA").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt1 = tx1.freeze_with(client).sign(operator_key).execute(client)
        token_id_1 = receipt1.token_id

        # Create Second Token
        tx2 = TokenCreateTransaction().set_token_name("Second Token").set_token_symbol("TKB").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt2 = tx2.freeze_with(client).sign(operator_key).execute(client)
        token_id_2 = receipt2.token_id

        print(f"✅ Success! Created tokens: {token_id_1} and {token_id_2}")
    except Exception as e:
        print(f"❌ Error creating tokens: {e}")
        sys.exit(1)

    # 4. Associate the tokens with the new account
    # =================================================================
    print(f"\nSTEP 3: Associating tokens with account {recipient_id}...")
    try:
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(recipient_id)
            .add_token_id(token_id_1)
            .add_token_id(token_id_2)
            .freeze_with(client)
            .sign(recipient_key)  # Recipient must sign to approve
            .execute(client)
        )
        print(f"✅ Success! Token association complete. Status: {receipt.status}")
    except Exception as e:
        print(f"❌ Error associating tokens: {e}")
        sys.exit(1)

    # 5. Dissociate the tokens from the new account
    # =================================================================
    print(f"\nSTEP 4: Dissociating tokens from account {recipient_id}...")
    try:
        receipt = (
            TokenDissociateTransaction()
            .set_account_id(recipient_id)
            .add_token_id(token_id_1)
            .add_token_id(token_id_2)
            .freeze_with(client)
            .sign(recipient_key) # Recipient must sign to approve
            .execute(client)
        )
        print(f"✅ Success! Token dissociation complete.")
    except Exception as e:
        print(f"❌ Error dissociating tokens: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_dissociate()