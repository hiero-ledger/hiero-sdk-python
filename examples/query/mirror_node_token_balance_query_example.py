"""
MirrorNodeTokenBalanceQuery Example.

This example demonstrates how to:
1. Set up a client connection to the Hedera network.
2. Create a fungible token and query its balance.
3. Create a non-fungible token (NFT), mint an NFT, and query its balance.

This example waits before querying balances to allow the Mirror Node to catch up.

Run with:
  uv run python examples/query/mirror_node_token_balance_query.py
  python examples/query/mirror_node_token_balance_query.py
"""

import sys
import time

from hiero_sdk_python import Client
from hiero_sdk_python.query.mirror_node_token_balance_query import (
    MirrorNodeTokenBalanceQuery,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_type import TokenType


MIRROR_NODE_WAIT_SECONDS = 60


def setup_client() -> Client:
    """Create a client using the configured environment variables."""
    try:
        client = Client.from_env()
        print(f"Client initialized with operator ID: {client.operator_account_id}")
        return client
    except ValueError as exc:
        print(f"Failed to initialize client: {exc}")
        sys.exit(1)


def create_fungible_token(client: Client):
    """Create a fungible token and return its token ID."""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_treasury_account_id(client.operator_account_id)
        .set_decimals(2)
        .set_initial_supply(10)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")

    token_id = receipt.token_id
    print(f"Fungible token created: {token_id}")

    return token_id


def create_nft(client: Client):
    """Create a non-fungible token and return its token ID."""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_treasury_account_id(client.operator_account_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(10)
        .set_supply_key(client.operator_private_key)
        .freeze_with(client)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")

    token_id = receipt.token_id
    print(f"NFT created: {token_id}")

    return token_id


def mint_nft(client: Client, token_id) -> None:
    """Mint an NFT and print its serial number."""
    receipt = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_metadata(b"My NFT Metadata 1")
        .freeze_with(client)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")

    print(f"NFT minted with serial number: {receipt.serial_numbers}")


def query_token_balance(client: Client, token_id) -> None:
    """Query and print the operator account's balance for a token."""
    token_balance = (
        MirrorNodeTokenBalanceQuery().set_account_id(client.operator_account_id).set_token_id(token_id).execute(client)
    )

    print(f"Token ID: {token_balance.token_id}")
    print(f"Balance: {token_balance.balance}")
    print(f"Decimals: {token_balance.decimals}")


def main() -> None:
    """Run the MirrorNodeTokenBalanceQuery example."""
    client = setup_client()

    try:
        # Create a fungible token and query its balance.
        fungible_token_id = create_fungible_token(client)

        print(f"Waiting {MIRROR_NODE_WAIT_SECONDS} seconds for the Mirror Node to record the transaction...")
        time.sleep(MIRROR_NODE_WAIT_SECONDS)

        print("\nFungible token balance:")
        query_token_balance(client, fungible_token_id)

        # Create an NFT, mint it, and query its balance.
        nft_token_id = create_nft(client)
        mint_nft(client, nft_token_id)

        print(f"\nWaiting {MIRROR_NODE_WAIT_SECONDS} seconds for the Mirror Node to record the transactions...")
        time.sleep(MIRROR_NODE_WAIT_SECONDS)

        print("\nNFT token balance:")
        query_token_balance(client, nft_token_id)

    except Exception as exc:
        print(f"Example failed: {exc}", file=sys.stderr)
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
