"""
This example creates an infinite fungible token using Hiero SDK Python.

It:
1. Loads environment variables.
2. Sets up a client and operator.
3. Generates admin and supply keys on the fly.
4. Builds, signs, and executes a TokenCreateTransaction.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY

Usage:
uv run examples/token_create_fungible_infinite.py
python examples/token_create_fungible_infinite.py
"""

import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    Network,
    TokenType,
    SupplyType,
)


def setup_client():
    """Set up network and operator client."""
    load_dotenv()
    print("Connecting to Hedera testnet...")
    network = Network(network='testnet')
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_keys():
    """Generate new admin and supply keys."""
    print("\nGenerating new admin and supply keys for the token...")
    admin_key = PrivateKey.generate_ed25519()
    supply_key = PrivateKey.generate_ed25519()
    print("Keys generated successfully.")
    return admin_key, supply_key


def build_transaction(client, operator_id, admin_key, supply_key):
    """Build and freeze the infinite fungible token creation transaction."""
    print("\nBuilding transaction to create an infinite fungible token...")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Infinite Fungible Token")
        .set_token_symbol("IFT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_admin_key(admin_key)
        .set_supply_key(supply_key)
        .freeze_with(client)
    )
    return transaction


def execute_transaction(transaction, client, operator_key, admin_key, supply_key):
    """Sign and execute the transaction."""
    print("Signing transaction...")
    transaction.sign(operator_key)
    transaction.sign(admin_key)
    transaction.sign(supply_key)

    print("Executing transaction...")
    try:
        receipt = transaction.execute(client)
        if receipt and receipt.token_id:
            print(f"Success! Infinite fungible token created with ID: {receipt.token_id}")
        else:
            print("Token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Token creation failed: {e}")
        sys.exit(1)


def create_token_fungible_infinite():
    """Main function to create an infinite fungible token."""
    client, operator_id, operator_key = setup_client()
    admin_key, supply_key = generate_keys()
    transaction = build_transaction(client, operator_id, admin_key, supply_key)
    execute_transaction(transaction, client, operator_key, admin_key, supply_key)


if __name__ == "__main__":
    create_token_fungible_infinite()
