# uv run examples/token_delete.py
# python examples/token_delete.py

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
    TokenType,

)
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
import examples.token_mint_non_fungible as nft


# Load environment variables from .env file
load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

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
    account_private_key = PrivateKey.generate(os.getenv('KEY_TYPE', 'ed25519'))
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

# create NFT Collection to retrieve balances
def create_nft_collection(operator_id, operator_key, client):
    """ Create the NFT Collection (Token) """
    supply_key = nft.generate_supply_key()
    print("\nSTEP 2: Creating a new NFT collection...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("My Awesome NFT")
            .set_token_symbol("MANFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            # Use provided treasury_account_id if given, otherwise fall back to operator
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
        return token_id, supply_key
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
        print(f"💰 HBAR Balance for {account_id}: {account_balance.hbars} hbars")
        # Display token balances
        print("💎 Token Balances:")
        for token_id, balance in account_balance.token_balances.items():
            print(f"   - Token ID {token_id}: {balance} units")
        return account_balance
    except (ValueError, TypeError, RuntimeError, ConnectionError) as error:
        print(f"Error retrieving account balance: {error}")
        sys.exit(1)

def compare_token_balances(client, treasury_id: AccountId, receiver_id: AccountId, token_id: str):
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
    # Create the NFT collection with the test account as the treasury so minted NFTs
    # will be owned by the test account and show up in its token balances.
    token_id, supply_key = create_nft_collection(
        test_account_id,
        test_account_key,
        client)
    #imported method from example/token_mint_non_fungible.py
    # to mint NFTs for the test account
    nft.token_mint_non_fungible(client, token_id, supply_key)

    get_account_balance(client, test_account_id)
    #OPTIONAL comparison of token balances between test account and operator account
    compare_token_balances(client, test_account_id, client.operator_account_id, token_id)

if __name__ == "__main__":
    main()
