# uv run examples/query/account_balance_query_2.py
# python examples/query/account_balance_query_2.py

"""Example: Use CryptoGetAccountBalanceQuery to retrieve an account's
HBAR and token balances, including minting NFTs to the account."""

import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
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


# Load environment variables from .env file
load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()
key_type = os.getenv('KEY_TYPE', 'ecdsa')

def setup_client():
    """Setup Client """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # Get the operator account from the .env file
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        # Set the operator (payer) account for the client
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client
    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

def create_account(client, name, initial_balance=Hbar(10)):
    """Create a test account with initial balance"""
    account_private_key = PrivateKey.generate(key_type)
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
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
    """Create an NFT collection and mint metadata_list (default 3 items)."""
    metadata_list = [b"METADATA_A", b"METADATA_B", b"METADATA_C"]

    try:
        supply_key = PrivateKey.generate(key_type)

        token_id = (
            TokenCreateTransaction()
            .set_token_name("My Awesome NFT").set_token_symbol("MANFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(treasury_account_id)
            .set_initial_supply(0)
            .set_supply_key(supply_key)
            .freeze_with(client)
            .sign(treasury_account_key).sign(supply_key).execute(client)
        ).token_id

        TokenMintTransaction() \
            .set_token_id(token_id).set_metadata(metadata_list) \
            .freeze_with(client).sign(supply_key).execute(client)

        total_supply = TokenInfoQuery().set_token_id(token_id).execute(client).total_supply
        print(f"✅ Created NFT {token_id} — total supply: {total_supply}")
        return token_id
    except (ValueError, TypeError, RuntimeError, ConnectionError) as error:
        print(f"❌ Error creating token: {error}")
        sys.exit(1)

def get_account_balance(client: Client, account_id: AccountId):
    """Get account balance using CryptoGetAccountBalanceQuery"""
    print(f"Retrieving account balance for account id: {account_id}  ...")
    try:
        # Use CryptoGetAccountBalanceQuery to get the account balance
        account_balance = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(client)
        )
        print("✅ Account balance retrieved successfully!")
        # Print account balance with account_id context
        print(f"💰 HBAR Balance for {account_id}: {account_balance.hbars} hbars")
        # Display token balances
        if account_balance.token_balances:
            print("💎 Token Balances:")
            for token_id, balance in account_balance.token_balances.items():
                print(f" - Token ID {token_id}: {balance} units")
        # Alternatively, you can use: print(account_balance)
        return account_balance
    except (ValueError, TypeError, RuntimeError, ConnectionError) as error:
        print(f"Error retrieving account balance: {error}")
        sys.exit(1)

#OPTIONAL comparison function
def compare_token_balances(client, treasury_id: AccountId,
                           receiver_id: AccountId,
                           token_id: TokenId):
    """Compare token balances between two accounts"""
    print(
        f"\n🔎 Comparing token balances for Token ID {token_id} "
        f"between accounts {treasury_id} and {receiver_id}..."
    )
    # retrieve balances for both accounts
    treasury_balance = get_account_balance(client, treasury_id)
    receiver_balance = get_account_balance(client, receiver_id)
    # extract token balances
    treasury_token_balance = treasury_balance.token_balances.get(token_id, 0)
    receiver_token_balance = receiver_balance.token_balances.get(token_id, 0)
    # print results
    print(f"🏷️ Token balance for Treasury ({treasury_id}): {treasury_token_balance}")
    print(f"🏷️ Token balance for Receiver ({receiver_id}): {receiver_token_balance}")

def main():
    """Main function to run the account balance query example
    1-Create test account with intial balance
    2- Create NFT collection with test account as treasury
    3- Mint NFTs to the test account
    4- Retrieve and display account balances including token balances

    """
    client = setup_client()
    test_account_id, test_account_key = create_account(client, "Test Account")
    # Create the tokens with the test account as the treasury so minted tokens
    # will be owned by the test account and show up in its token balances.
    token_id = create_and_mint_token(
        test_account_id,
        test_account_key,
        client)
    # Retrieve and display account balance for the test account
    get_account_balance(client, test_account_id)
    #OPTIONAL comparison of token balances between test account and operator account
    compare_token_balances(client, test_account_id, client.operator_account_id, token_id)

if __name__ == "__main__":
    main()
