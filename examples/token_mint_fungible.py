"""
Creates a mintable fungible token and then mints additional supply.
"""

"""
uv run examples/token_mint_fungible.py
python examples/token_mint_fungible.py

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
    TokenMintTransaction,
)

# Load environment variables from .env file
load_dotenv()

def setup_client():
    """Setup Client"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)



def generate_supply_key():
    """Generate a new supply key for the token."""
    print("\nSTEP 1: Generating a new supply key...")
    supply_key = PrivateKey.generate("ed25519")
    print("✅ Supply key generated.")
    return supply_key

def create_new_token():
    """Create a token with the supply key"""
    client, operator_id, operator_key = setup_client()
    supply_key = generate_supply_key()
    print("\nSTEP 2: Creating a new mintable token...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("Mintable Fungible Token")
            .set_token_symbol("MFT")
            .set_initial_supply(100)  # Start with 100 tokens
            .set_decimals(2)
            .set_treasury_account_id(operator_id)
            .set_supply_key(supply_key)  # Assign the supply key
        )
        
        # Freeze, sign with BOTH operator and the new supply key, then execute
        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(supply_key)  # The new supply key must sign to give consent
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
        return client, token_id, supply_key
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def token_mint_fungible():
    """Mint more of a fungible token."""

    client, token_id, supply_key = create_new_token()
    mint_amount = 5000 # This is 50.00 tokens because decimals is 2
    print(f"\nSTEP 3: Minting {mint_amount} more tokens for {token_id}...")
    try:
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_amount(mint_amount)
            .freeze_with(client)
            .sign(supply_key)  # Must be signed by the supply key
            .execute(client)
        )
        # THE FIX: The receipt confirms status, it does not contain the new total supply.
        print(f"✅ Success! Token minting complete.")
    except Exception as e:
        print(f"❌ Error minting tokens: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_mint_fungible()
