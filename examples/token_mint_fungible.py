import os
import sys
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

def fungible_token_mint():
    """
    Mint fungible tokens to increase the total supply of the token.
    The new supply must be lower than 2^63-1 (within the range that can be safely stored in a signed 64-bit integer).

    Loads environment variables for OPERATOR_ID, OPERATOR_KEY, SUPPLY_KEY, TOKEN_ID.
    Creates and signs a TokenMintTransaction for a fungible token.
    Submits the transaction and prints the result.
    """

    network = Network(network='testnet')
    client = Client(network)

    payer_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    payer_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    supply_key = PrivateKey.from_string_ed25519(os.getenv('SUPPLY_KEY'))
    token_id = TokenId.from_string(os.getenv('TOKEN_ID'))

    client.set_operator(payer_id, payer_key)

    # Example: If the token has 2 decimals, "20000" here means 200.00 tokens minted.
    transaction = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_amount(20000) # Positive, non-zero amount to mint in lowest denomination
        .freeze_with(client)
        .sign(payer_key)
        .sign(supply_key)
    )
    
    try:
        receipt = transaction.execute(client)
        if receipt and receipt.tokenId:
            print(f"Fungible token minting successful")
        else:
            print(f"Fungible token minting failed")
            sys.exit(1)
    except Exception as e:
        print(f"Fungible token minting failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    fungible_token_mint() 
