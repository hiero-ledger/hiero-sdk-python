"""
uv run examples/tokens/token_update_transaction_nft.py
python examples/tokens/token_update_transaction_nft.py

"""

import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateTransaction

def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def create_nft(client, operator_id, operator_key, metadata_key):
    """
    Create a non-fungible token

    If we want to update metadata later using TokenUpdateTransaction:
    1. Set a metadata_key and sign the update transaction with it, or
    2. Sign the update transaction with the admin_key

    Note: If no Admin Key was assigned during token creation (immutable token),
    token updates will fail with TOKEN_IS_IMMUTABLE.
    """
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
        .set_freeze_key(operator_key)
        .set_supply_key(operator_key)
        .set_metadata_key(metadata_key)
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


def get_nft_info(client, nft_token_id):
    """Get information about an NFT"""
    info = TokenInfoQuery().set_token_id(nft_token_id).execute(client)

    return info


def update_nft_data(
    client,
    nft_token_id,
    update_metadata,
    update_token_name,
    update_token_symbol,
    update_token_memo,
):
    """Update data for an NFT"""
    receipt = (
        TokenUpdateTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(update_metadata)
        .set_token_name(update_token_name)
        .set_token_symbol(update_token_symbol)
        .set_token_memo(update_token_memo)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"NFT data update failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Successfully updated NFT data")


def token_update_nft():
    """
    Demonstrates the NFT token update functionality by:
    1. Setting up client with operator account
    2. Creating a non-fungible token with metadata key
    3. Checking the current NFT info
    4. Updating the token's metadata, name, symbol and memo
    5. Verifying the updated NFT info
    """

    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    # Create metadata key
    metadata_private_key = PrivateKey.generate_ed25519()

    nft_token_id = create_nft(client, operator_id, operator_key, metadata_private_key)

    print("\nNFT info before update:")
    nft_info = get_nft_info(client, nft_token_id)
    print(nft_info)

    # New data to update the NFT
    update_metadata = b"Updated metadata"
    update_token_name = "Updated NFT"
    update_token_symbol = "UPD"
    update_token_memo = "Updated memo"

    update_nft_data(
        client,
        nft_token_id,
        update_metadata,
        update_token_name,
        update_token_symbol,
        update_token_memo,
    )

    print("\nNFT info after update:")
    nft_info = get_nft_info(client, nft_token_id)
    print(nft_info)


if __name__ == "__main__":
    token_update_nft()
