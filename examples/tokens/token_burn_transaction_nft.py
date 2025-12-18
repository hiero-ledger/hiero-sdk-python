"""
uv run examples/tokens/token_burn_transaction_nft.py
python examples/tokens/token_burn_transaction_nft.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client, operator_id, operator_key


def create_nft(client, operator_id, operator_key):
    """Create a non-fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .execute(client)
    )

    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    # Get token ID from receipt
    nft_token_id = receipt.token_id
    print(f"NFT created with ID: {nft_token_id}")

    return nft_token_id


def mint_nfts(client, nft_token_id, metadata_list):
    """Mint a non-fungible token"""
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(metadata_list)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT minted with serial numbers: {receipt.serial_numbers}")

    return receipt.serial_numbers


def get_token_info(client, token_id):
    """Get token info for the token"""
    token_info = TokenInfoQuery().set_token_id(token_id).execute(client)

    print(f"Token supply: {token_info.total_supply}")


def token_burn_nft():
    """
    Demonstrates the NFT burn functionality by:
    1. Setting up client with operator account
    2. Creating an NFT collection with the operator account as owner
    3. Minting multiple NFTs with metadata
    4. Getting initial token supply
    5. Burning specific NFTs by serial number
    6. Getting final token supply to verify burn
    """
    client, operator_id, operator_key = setup_client()

    # Create a fungible token with the treasury account as owner and signer
    token_id = create_nft(client, operator_id, operator_key)

    # Mint 4 NFTs
    metadata_list = [b"metadata1", b"metadata2", b"metadata3", b"metadata4"]
    serial_numbers = mint_nfts(client, token_id, metadata_list)

    # Get and print token balances before burn to show the initial state
    print("\nToken balances before burn:")
    get_token_info(client, token_id)

    # Burn first 2 NFTs from the minted collection (serials 1 and 2)
    receipt = (
        TokenBurnTransaction()
        .set_token_id(token_id)
        .set_serials(serial_numbers[0:2])
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT burn failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(
        f"Successfully burned NFTs with serial numbers {serial_numbers[0:2]} from {token_id}"
    )

    # Get and print token balances after burn to show the final state
    print("\nToken balances after burn:")
    get_token_info(client, token_id)


if __name__ == "__main__":
    token_burn_nft()
