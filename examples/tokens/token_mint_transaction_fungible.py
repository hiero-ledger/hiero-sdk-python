# uv run examples/tokens/token_mint_fungible.py
# python examples/tokens/token_mint_fungible.py
"""
uv run examples/tokens/token_mint_transaction_fungible.py
python examples/tokens/token_mint_transaction_fungible.py

Creates a mintable fungible token and then mints additional supply.
"""

import os
import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenInfoQuery,
    ResponseCode,
)

def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def generate_supply_key():
    """Generate a new supply key for the token."""
    print("\nSTEP 1: Generating a new supply key...")
    supply_key = PrivateKey.generate(os.getenv("KEY_TYPE", "ed25519"))
    print("✅ Supply key generated.")
    return supply_key


def create_new_token(client):
    """
    Create a fungible token that can have its supply changed (minted or burned).
    This requires setting a supply key, which is a special key that authorizes supply changes.
    """

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

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
        if getattr(info, "supply_key", None):
            print("✅ Verified: Token has a supply key set.")
        else:
            print("❌ Warning: Token does not have a supply key set.")

        return token_id, supply_key
    except (ValueError, TypeError) as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def token_mint_fungible(client, token_id, supply_key):
    """
    Mint more of a fungible token

    The token must have a supply key set during creation, which authorizes future minting or burning.
    Only the holder of the supply key can perform these actions.
    """

    mint_amount = 5000  # This is 50.00 tokens because decimals is 2
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
        print(
            f"✅ Success! Token minting complete, Status: {ResponseCode(receipt.status).name}"
        )

        # Confirm total supply after minting
        info_after = TokenInfoQuery().set_token_id(token_id).execute(client)
        print(f"Total supply after minting: {info_after.total_supply}")
    except (ValueError, TypeError) as e:
        print(f"❌ Error minting tokens: {e}")
        sys.exit(1)


def main():
    """
    1. Create a new token with a supply key so its supply can be changed later
    2. Confirm the token's total supply before minting
    3. Mint more tokens by submitting a TokenMintTransaction (signed by the supply key)
    4. Confirm the token's total supply after minting
    """

    client = setup_client()
    token_id, supply_key = create_new_token(client)
    token_mint_fungible(client, token_id, supply_key)


if __name__ == "__main__":
    main()
