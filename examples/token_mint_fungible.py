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
    TokenInfoQuery
    
)

# Load environment variables from .env file
load_dotenv()

def setup_client():
    """Setup Client"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)



def generate_supply_key():
    """Generate a new supply key for the token."""
    print("\nSTEP 1: Generating a new supply key...")
    supply_key = PrivateKey.generate_ed25519()
    print("✅ Supply key generated.")
    return supply_key

def create_new_token():
    """
    Create a fungible token that can have its supply changed (minted or burned).
    This requires setting a supply key, which is a special key that authorizes supply changes.
    """
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
            .set_supply_key(supply_key)  # Assign the supply key to enable mint/burn
        )
        # The transaction must be signed by both the treasury (operator) and the supply key
        # to authorize creation and future supply changes.
        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(supply_key)  # The new supply key must sign to give consent
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")

        # Confirm the token has a supply key set
        info = TokenInfoQuery().set_token_id(token_id).execute(client)
        if getattr(info, 'supply_key', None):
            print("✅ Verified: Token has a supply key set.")
        else:
            print("❌ Warning: Token does not have a supply key set.")

        return client, token_id, supply_key
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def token_mint_fungible():
    """
    Mint more of a fungible token

    1. Create a new token with a supply key so its supply can be changed later
    2. Confirm the token's total supply before minting
    3. Mint more tokens by submitting a TokenMintTransaction (signed by the supply key)
    4. Confirm the token's total supply after minting

    The token must have a supply key set during creation, which authorizes future minting or burning.
    Only the holder of the supply key can perform these actions.
    """

    # Create a new token with a supply key so its supply can be changed later
    client, token_id, supply_key = create_new_token()

    mint_amount = 5000 # This is 50.00 tokens because decimals is 2
    print(f"\nSTEP 3: Minting {mint_amount} more tokens for {token_id}...")

    # Confirm total supply before minting
    info_before = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Total supply before minting: {info_before.total_supply}")

    try:
        # Minting requires a transaction signed by the supply key
        # Without the supply key, the token supply is fixed and cannot be changed
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_amount(mint_amount)
            .freeze_with(client)
            .sign(supply_key)  # Must be signed by the supply key
            .execute(client)
        )
        print(f"✅ Success! Token minting complete.")

        # Confirm total supply after minting
        info_after = TokenInfoQuery().set_token_id(token_id).execute(client)
        print(f"Total supply after minting: {info_after.total_supply}")
    except Exception as e:
        print(f"❌ Error minting tokens: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_mint_fungible()
