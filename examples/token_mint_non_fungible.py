"""
uv run examples/token_mint_non_fungible.py
python examples/token_mint_non_fungible.py

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
    TokenType,
)

# Load environment variables from .env file
load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()

def token_mint_non_fungible():
    """
    Creates an NFT collection and then mints new NFTs with metadata.
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

    # 2. Generate a Supply Key
    # =================================================================
    print("\nSTEP 1: Generating a new supply key...")
    supply_key = PrivateKey.generate("ed25519")
    print("✅ Supply key generated.")

    # 3. Create the NFT Collection (Token)
    # =================================================================
    print("\nSTEP 2: Creating a new NFT collection...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("My Awesome NFT")
            .set_token_symbol("MANFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(operator_id)
            .set_initial_supply(0)  # NFTs must have an initial supply of 0
            .set_supply_key(supply_key)  # Assign the supply key for minting
        )
        
        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(supply_key)  # The new supply key must sign to give consent
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created NFT collection with Token ID: {token_id}")
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

    # 4. Mint new NFTs with metadata
    # =================================================================
    # Define metadata directly in the script instead of loading from a file
    metadata_list = [
        b"METADATA_A",
        b"METADATA_B",
        b"METADATA_C",
    ]
    print(f"\nSTEP 3: Minting {len(metadata_list)} new NFTs for token {token_id}...")
    try:
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata(metadata_list) # Set the list of metadata
            .freeze_with(client)
            .sign(supply_key)  # Must be signed by the supply key
            .execute(client)
        )
        
        # THE FIX: The receipt confirms status, it does not contain serial numbers.
        print(f"✅ Success! NFT minting complete.")

    except Exception as e:
        print(f"❌ Error minting NFTs: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_mint_non_fungible()