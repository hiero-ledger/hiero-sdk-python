"""
uv run examples/query/token_info_query_nft.py
python examples/query/token_info_query_nft.py
"""

import sys

from hiero_sdk_python import (
    Client,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction


def setup_client():
    """Initialize client using environment configuration"""
    print("Connecting to Hedera network using environment configuration...")

    client = Client.from_env()

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    if not operator_id or not operator_key:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY must be set in the environment"
        )

    print(f"Client set up with operator id {operator_id}")
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
        .set_freeze_key(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"NFT creation failed with status: "
            f"{ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    nft_token_id = receipt.token_id
    print(f"NFT created with ID: {nft_token_id}")

    return nft_token_id


def query_token_info():
    """
    Demonstrates the token info query functionality.
    """
    client, operator_id, operator_key = setup_client()

    token_id = create_nft(client, operator_id, operator_key)

    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Non-fungible token info: {info}")


if __name__ == "__main__":
    query_token_info()
