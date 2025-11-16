"""
This example creates a fungible token with on-ledger metadata using Hiero SDK Python.

It demonstrates:
1. Creating a token with on-ledger metadata.
2. Attempting to update metadata WITHOUT a metadata_key: expected to fail.
3. Attempting to update metadata WITH a metadata_key: expected to succed.
4. Demonstrates that metadata longer than 100 bytes is rejected.

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
    TokenUpdateTransaction,
    Network,
    TokenType,
    SupplyType,
)
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key

    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def get_receipt(executable, client):
    """Executes a transaction, returns a receipt or exits on failure."""
    try:
        receipt = executable.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Transaction failed with status: {receipt.status.name}")
            sys.exit(1)
        return receipt
    except Exception as e:
        print(f"Transction execution failed: {e}")
        sys.exit(1)


def create_token_without_metadata_key(client, operator_key, operator_id):
    """
    Creating token with on-ledger metadata WITHOUT metadata_key (max 100 bytes)
    """
    print("\nCreating token WITHOUT metadata_key")

    metadata = b"Initial on-ledger metadata"  # < 100 bytes

    try:
        transaction = (
            TokenCreateTransaction()
            .set_token_name("MetadataToken_NoKey")
            .set_token_symbol("MDN")
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.INFINITE)
            .set_initial_supply(10)
            .set_metadata(metadata)
            .freeze_with(client)
        )
    except Exception as e:
        print(f"Error while building create transaction: {e}")
        sys.exit(1)

    # Sign + execute
    transaction.sign(operator_key)
    receipt = get_receipt(transaction, client)

    print(f"Token created (no metadata_key) with metadata: {metadata!r}")
    return receipt.token_id


def try_update_metadata_without_key(client, operator_key, token_id):
    print("\nAttempting metadata update WITHOUT metadata_key...")
    updated_metadata = b"updated metadata (without metadata_key)"
    try:
        update_transaction = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(updated_metadata)
            .freeze_with(client)
        )
        update_transaction.sign(operator_key)
        receipt = update_transaction.execute(client)
        status = getattr(receipt.status, "name", str(receipt.status))

        if receipt.status == ResponseCode.SUCCESS:
            print(
                f"Unexpected SUCCESS. Status: {receipt.status}"
                "(this should normally fail when metadata_key is missing)"
            )
        else:
            print(f"Expected failure: metadata update rejected -> status={status}")

    except Exception as e:
        print(f"Failed: {e}")


def create_token_with_metadata_key(client, operator_id, operator_key):
    """
    Create token with metadata_key and on-ledger metadata (max 100 bytes)
    """
    metadata_key = PrivateKey.generate()
    metadata = b"Example on-ledger token metadata"

    print("\nCreating token with metadata and metadata_key...")
    try:
        transaction = (
            TokenCreateTransaction()
            .set_token_name("Metadata Fungible Token")
            .set_token_symbol("MFT")
            .set_decimals(2)
            .set_initial_supply(1000)
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.INFINITE)
            .set_metadata_key(metadata_key)
            .set_metadata(metadata)
            .freeze_with(client)
        )
    except Exception as e:
        print(f"Error while building create transaction: {e}")
        sys.exit(1)

    transaction.sign(operator_key)
    transaction.sign(metadata_key)
    receipt = get_receipt(transaction, client)

    print(f"Token created with metadat_key: {metadata_key.public()}")
    print(f"Metadata set on transaction: {metadata!r}")
    return receipt.token_id, metdata_key


def update_metadata_with_key(client, token_id, operator_key, metadata_key):
    """
    Update token metadata with metadata_key
    """
    print("\nUpdating metadata WITH metadata_key...")
    upodated_metadata = b"Updated metdata (with key)"

    try:
        update_tx = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(updated_metadata)
            .freeze_with(client)
        )
    except Exception as e:
        print(f"Error while freezing update transaction: {e}")
        sys.exit(1)

    update_tx.sign(operator_key)
    update_tx.sign(metadata_key)

    receipt = get_receipt(update_tx, client)
    print(f"Metadata successfully updated: {metadata!r}")


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
        print(
            "Error: Expected ValueError for metadata > 100 bytes, but none was raised."
        )
    except ValueError as exc:
        print(f"Expected error raised for metadata > 100 bytes: {exc}")


def create_token_with_metadata():
    """
    Main function to create and update fungible token with metadata with two scenarios:
    - create token WITHOUT metadat_key (expected to fail)
    - create token WITH metadat_key (expected to succed)
    and validate metadata length
    """
    client, operator_id, operator_key = setup_client()

    token_a = create_token_without_metadata_key(client, operator_key, operator_id)
    try_update_metadata_without_key(client, operator_key, token_a)

    token_b, metadata_key = create_token_with_metadata_key(
        client, operator_key, operator_id
    )
    update_metadata_with_key(client, token_b, operator_key, metadata_key)

    demonstrate_metadata_length_validation(client, operator_id)


if __name__ == "__main__":
    create_token_with_metadata()
