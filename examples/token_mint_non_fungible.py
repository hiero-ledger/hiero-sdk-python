import os
import sys
import json
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenMintTransaction,
    Network,
    TokenId,
)

load_dotenv()

def nft_token_mint(metadata):
    """
    Minting a non-fungible token creates new NFTs for the token ID by providing metadata as a list of byte arrays.
    
    Loads environment variables for OPERATOR_ID, OPERATOR_KEY, SUPPLY_KEY, TOKEN_ID.
    Creates and signs a TokenMintTransaction for a NON_FUNGIBLE_UNIQUE token.
    Submits the transaction and prints the result.
    """

    network = Network(network='testnet')
    client = Client(network)

    payer_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    payer_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    supply_key = PrivateKey.from_string_ed25519(os.getenv('SUPPLY_KEY'))
    token_id = TokenId.from_string(os.getenv('TOKEN_ID'))

    client.set_operator(payer_id, payer_key)

    transaction = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_metadata(metadata) # Mandatory single or list of byte array metadata for NFTs each up to 100 bytes e.g. b"A"
        .freeze_with(client)
        .sign(payer_key)
        .sign(supply_key)
        
    )
    
    try:
        receipt = transaction.execute(client)
        if receipt and receipt.tokenId:
            print(f"NFT minting successful")
        else:
            print(f"NFT minting failed")
            sys.exit(1)
    except Exception as e:
        print(f"NFT minting failed: {str(e)}")
        sys.exit(1)


def load_metadata_from_json(file_path):
    """
    Loads NFT metadata from a JSON file to use in the transaction.
    :param file_path: Path to the JSON file containing metadata.
    :return: List of byte arrays representing NFT metadata.
    """
    try:
        with open(file_path, 'r') as file:
            metadata = json.load(file)
            if not isinstance(metadata, list):
                raise ValueError("Metadata JSON must be a list of strings.")
            # Convert each metadata string to bytes
            return [m.encode('utf-8') for m in metadata]
    except Exception as e:
        print(f"Failed to load metadata from JSON: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    metadata = load_metadata_from_json("nft_metadata.json")
    nft_token_mint(metadata) 

