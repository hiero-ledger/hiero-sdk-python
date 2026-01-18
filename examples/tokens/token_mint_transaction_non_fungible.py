# uv run examples/tokens/token_mint_non_fungible.py
# python examples/tokens/token_mint_non_fungible.py

"""
Create a Non-Fungible Token (NFT) Collection and Mint NFTs
uv run examples/token_mint_transaction_non_fungible.py
python examples/token_mint_transaction_non_fungible.py
"""

import os
import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenType,
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
    supply_key = PrivateKey.generate(os.getenv("HSDK_KEY_TYPE", "ed25519"))
    print("✅ Supply key generated")
    return supply_key


def create_nft_collection():
    """Create the NFT Collection (Token)"""

    client = setup_client()

    supply_key = generate_supply_key()
    print("\nSTEP 2: Creating a new NFT collection...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("My Awesome NFT")
            .set_token_symbol("MANFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(client.operator_account_id)
            .set_initial_supply(0)  # NFTs must have an initial supply of 0
            .set_supply_key(supply_key)  # Assign the supply key for minting
        )

        receipt = (
            tx.freeze_with(client)
            .sign(client.operator_private_key)
            .sign(supply_key)  # The new supply key must sign to give consent
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created NFT collection with Token ID: {token_id}")
        return client, token_id, supply_key
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def token_mint_non_fungible(client, token_id, supply_key):
    """
    Mint new NFTs with metadata

    The supply key authorizes minting new NFTs after the collection is created.
    Each NFT is assigned unique metadata, which can be used to identify or describe the token.
    """

    # Prepare the metadata for each NFT to be minted
    # Each entry in the list will become a unique NFT with its own metadata
    metadata_list = [
        b"METADATA_A",
        b"METADATA_B",
        b"METADATA_C",
    ]
    print(f"\nSTEP 3: Minting {len(metadata_list)} new NFTs for token {token_id}...")
    # Confirm total supply before minting
    info_before = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Total supply before minting: {info_before.total_supply}")
    try:
        # Mint the NFTs by submitting a TokenMintTransaction
        # The transaction must be signed by the supply key to authorize minting
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata(metadata_list)  # Set the list of metadata
            .freeze_with(client)
            .sign(supply_key)  # Must be signed by the supply key
            .execute(client)
        )

        # THE FIX: The receipt confirms status, it does not contain serial numbers.
        print(
            f"✅ Success! NFT minting complete, Status: {ResponseCode(receipt.status).name}"
        )
        # Confirm total supply after minting
        info_after = TokenInfoQuery().set_token_id(token_id).execute(client)
        print(f"Total supply after minting: {info_after.total_supply}")
    except (ValueError, TypeError) as e:
        print(f"❌ Error minting NFTs: {e}")
        sys.exit(1)


def main():
    """
    1. Create a new NFT collection (token) with a supply key
    2. Prepare metadata for each NFT to be minted
    3. Confirm total supply before minting
    4. Mint the NFTs by submitting a TokenMintTransaction (signed by the supply key)
    5. Confirm total supply after minting
    """
    client, token_id, supply_key = create_nft_collection()
    token_mint_non_fungible(client, token_id, supply_key)


if __name__ == "__main__":
    main()
