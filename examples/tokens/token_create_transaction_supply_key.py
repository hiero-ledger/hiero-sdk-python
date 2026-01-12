"""
This example demonstrates the Purpose of the Supply Key for token management using Hiero SDK Python.

It shows:
1. Creating a FUNGIBLE token WITHOUT a supply key (Fixed Supply).
2. Attempting to mint more of that token (Fails, because no supply key exists).
3. Creating an NFT token WITH a supply key.
4. Successfully minting tokens using the supply key.
5. Verifying the supply using TokenInfoQuery.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY

Usage:
uv run examples/tokens/token_create_transaction_supply_key.py
"""

import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenInfoQuery,
)

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType



def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def create_token_no_supply_key(client, operator_id, operator_key):
    """
    Create a FUNGIBLE token WITHOUT a supply key.
    We use Fungible because creating an NFT without a supply key is forbidden
    (it would result in a permanently 0-supply, useless token).
    """
    print("\n--- Scenario 1: Token WITHOUT Supply Key ---")
    print("Creating a Fungible token with NO supply key (Fixed Supply)...")

    transaction = (
        TokenCreateTransaction()
        .set_token_name("Fixed Supply Token")
        .set_token_symbol("FST")
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_initial_supply(1000)
        .set_decimals(0)
        .set_treasury_account_id(operator_id)
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        reciept = transaction.execute(client)
        if reciept.status != ResponseCode.SUCCESS:
            print(
                f"Token creation failed with status: {ResponseCode(reciept.status).name}"
            )
            sys.exit(1)

        token_id = reciept.token_id
        print(f" ✅ Token created successfully with ID: {token_id}")
        return token_id

    except Exception as e:
        print(f"Error during token creation as: {e}.")
        sys.exit(1)


def demonstrate_mint_fail(client, token_id):
    """
    Attempt to mint more tokens when no supply key exists.
    This is expected to FAIL.
    """
    print(f"Attempting to mint more to {token_id} (Expected to FAIL)...")

    transaction = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_amount(100)  # Trying to mint 100 more fungible tokens
        .freeze_with(client)
    )

    try:
        receipt = transaction.execute(client)
        if receipt.status == ResponseCode.TOKEN_HAS_NO_SUPPLY_KEY:
            print(
                f" -->  Mint failed as expected! Status: {ResponseCode(receipt.status).name}"
            )
        else:
            print(f"Mint failed with status: {ResponseCode(receipt.status).name}")

    except Exception as e:
        print(f"✅ Mint failed as expected! Error: {e}")


def create_token_with_supply_key(client, operator_id, operator_key):
    """
    Create a Non-Fungible token (NFT) WITH a supply key.
    """
    print("\n--- Scenario 2: Token WITH Supply Key ---")

    # Generate a specific supply key
    supply_key = PrivateKey.generate_ed25519()
    print(" ---> Generated new Supply Key.")

    print(" ---> Creating an NFT token WITH supply key...")

    transaction = (
        TokenCreateTransaction()
        .set_token_name("With Supply Key NFT")
        .set_token_symbol("WSK")
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_treasury_account_id(operator_id)
        .set_supply_key(supply_key)  # <--- Setting the supply key
        .freeze_with(client)
    )

    # Sign with operator  and supply key
    transaction.sign(operator_key)
    transaction.sign(supply_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"Token creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        token_id = receipt.token_id
        print(f" ✅ Token created successfully with ID: {token_id}")
        return token_id, supply_key

    except Exception as e:
        print(f"Error during token Creation as :{e}.")
        sys.exit(1)


def demonstrate_mint_success(client, token_id, supply_key):
    """
    Mint a token using the valid supply key.
    For NFTs, minting involve setting metadata for each unique serial number been created.
    """
    print(f"Attempting to mint NFT to {token_id} using Supply Key...")

    transaction = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_metadata([b"NFT Serial 1", b"NFT Serial 2"])
        .freeze_with(client)
    )

    ##  #### =>: Must sign with the supply key!
    transaction.sign(supply_key)

    receipt = transaction.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f" ❌ Mint failed with status: {ResponseCode(receipt.status).name}")
        return

    print(f"✅ Mint Successful! New Serials: {receipt.serial_numbers}")


def verify_token_info(client, token_id):
    """Query token info to see total supply."""
    print(f"Querying Token Info for {token_id}...")
    info = TokenInfoQuery().set_token_id(token_id).execute(client)

    print(f"  - Total Supply: {info.total_supply}")
    print(f"  - Supply Key Set: {info.supply_key is not None}")


def main():
    """
    Main execution flow.
    """
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    # 1. Demonstrate Failure (No Supply Key)
    # Note: Using Fungible token because NFT requires Supply Key at creation
    token_id_no_key = create_token_no_supply_key(client, operator_id, operator_key)
    demonstrate_mint_fail(client, token_id_no_key)

    # 2. Demonstrate Success (With Supply Key)
    token_id_with_key, supply_key = create_token_with_supply_key(
        client, operator_id, operator_key
    )
    demonstrate_mint_success(client, token_id_with_key, supply_key)
    verify_token_info(client, token_id_with_key)

    print("\n <--->  Supply key demonstration completed  <---> ")


if __name__ == "__main__":
    main()
