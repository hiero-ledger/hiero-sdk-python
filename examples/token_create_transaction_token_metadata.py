"""
This example creates a fungible token with on-ledger metadata using Hiero SDK Python.

It:
1. Loads environment variables.
2. Sets up a client and operator.
3. Generates admin and supply keys on the fly.
4. Builds, signs, and executes a TokenCreateTransaction.
5. Demonstrates that metadata lonmger than 100 bytes is rejected.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY

Usage:
uv run examples/token_create_transaction_token_metadata.py
python examples/token_create_transaction_token_metadata.py
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

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
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


def build_transaction_with_metadata(client, operator_id, admin_key, supply_key):
    """
    Build and freeze the fungible token creation transaction
    thath includes on-ledger metadata (max 100 bytes)
    """
    metadata = b"Example on-ledger token metadata"

    print("\nBuilding transaction to create a fungible token with metadata...")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Metadata Fungible Token")
        .set_token_symbol("MFT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_admin_key(admin_key)
        .set_supply_key(supply_key)
        .set_metadata(metadata)
        .freeze_with(client)
    )
    
    print(f"Metadata set on transaction: {metadata!r}")
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
            print(f"Success! Fungible token with metadata created with ID: {receipt.token_id}")
        else:
            print("Token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Token creation failed: {e}")
        sys.exit(1)


def demonstrate_metadata_length_validation(client, operator_id):
    """
    Demonstrate that metadata longer than 100 bytes trigger a ValueError
    in the TokenCreateTransaction.set_metadata() validation.
    """
    print("\nDemonstrating metadata length validation (> 100 bytes)...")
    too_long_metadata = b"x" * 101

    try:
        (
            TokenCreateTransaction()
            .set_token_name("TooLongMetadataToken")
            .set_token_symbol("TLM")
            .set_treasury_account_id(operator_id)
            .set_metadata(too_long_metadata)
        )
        print("Error: Expected ValueError for metadata > 100 bytes, but none was raised.")
    except ValueError as exc:
        print(f"Expected error raised for metadata > 100 bytes: {exc}")


def create_token_with_metadata():
    """
    Main function to create a fungible token with metadata
    and validate metadata length
    """
    client, operator_id, operator_key = setup_client()
    admin_key, supply_key = generate_keys()
    transaction = build_transaction_with_metadata(client, operator_id, admin_key, supply_key)
    execute_transaction(transaction, client, operator_key, admin_key, supply_key)
    demonstrate_metadata_length_validation(client, operator_id)


if __name__ == "__main__":
    create_token_with_metadata()
