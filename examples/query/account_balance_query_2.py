

"""Example: Use CryptoGetAccountBalanceQuery to retrieve an account's
HBAR and token balances, including minting NFTs to the account.
"""

import os
import sys

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    AccountCreateTransaction,
    Hbar,
    ResponseCode,
    TokenInfoQuery,
    TokenType,
    TokenMintTransaction,
)
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_id import TokenId


# Used for key generation (not client setup)
key_type = os.getenv("KEY_TYPE", "ecdsa")


def setup_client() -> Client:
    """Setup Client from environment variables."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_account(client, name, initial_balance=Hbar(10)):
    """Create a test account with initial balance"""
    account_private_key = PrivateKey.generate(key_type)
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(account_public_key)
        .set_initial_balance(initial_balance)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    account_id = receipt.account_id
    print(f"{name} account created with id: {account_id}")
    return account_id, account_private_key


def create_and_mint_token(treasury_account_id, treasury_account_key, client):
    """Create an NFT collection and mint metadata."""
    metadata_list = [b"METADATA_A", b"METADATA_B", b"METADATA_C"]

    try:
        supply_key = PrivateKey.generate(key_type)

        token_id = (
            TokenCreateTransaction()
            .set_token_name("My Awesome NFT")
            .set_token_symbol("MANFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(treasury_account_id)
            .set_initial_supply(0)
            .set_supply_key(supply_key)
            .freeze_with(client)
            .sign(treasury_account_key)
            .sign(supply_key)
            .execute(client)
        ).token_id

        TokenMintTransaction().set_token_id(token_id).set_metadata(
            metadata_list
        ).freeze_with(client).sign(supply_key).execute(client)

        total_supply = (
            TokenInfoQuery().set_token_id(token_id).execute(client).total_supply
        )
        print(f"✅ Created NFT {token_id} — total supply: {total_supply}")
        return token_id

    except (ValueError, TypeError, RuntimeError, ConnectionError) as error:
        print(f"❌ Error creating token: {error}")
        sys.exit(1)


def get_account_balance(client: Client, account_id: AccountId):
    """Get account balance using CryptoGetAccountBalanceQuery"""
    print(f"Retrieving account balance for account id: {account_id} ...")

    try:
        account_balance = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(client)
        )
        print("✅ Account balance retrieved successfully!")
        print(f"💰 HBAR Balance for {account_id}: {account_balance.hbars} hbars")
        return account_balance

    except (ValueError, TypeError, RuntimeError, ConnectionError) as error:
        print(f"Error retrieving account balance: {error}")
        sys.exit(1)


def compare_token_balances(
    client, treasury_id: AccountId, receiver_id: AccountId, token_id: TokenId
):
    """Compare token balances between two accounts"""
    print(
        f"\n🔎 Comparing token balances for Token ID {token_id} "
        f"between accounts {treasury_id} and {receiver_id}..."
    )

    treasury_balance = get_account_balance(client, treasury_id)
    receiver_balance = get_account_balance(client, receiver_id)

    treasury_token_balance = treasury_balance.token_balances.get(token_id, 0)
    receiver_token_balance = receiver_balance.token_balances.get(token_id, 0)

    print(f"🏷️ Token balance for Treasury ({treasury_id}): {treasury_token_balance}")
    print(f"🏷️ Token balance for Receiver ({receiver_id}): {receiver_token_balance}")


def main():
    """Run the account balance query example"""
    client = setup_client()

    test_account_id, test_account_key = create_account(client, "Test Account")

    token_id = create_and_mint_token(
        test_account_id, test_account_key, client
    )

    get_account_balance(client, test_account_id)

    compare_token_balances(
        client, test_account_id, client.operator_account_id, token_id
    )


if __name__ == "__main__":
    main()
