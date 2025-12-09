"""
Refactored example demonstrating transaction byte serialization and deserialization.

This example shows how to:
- Create and freeze a transaction
- Serialize to bytes (for storage, transmission, or signing)
- Deserialize from bytes
- Sign a deserialized transaction
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
    Transaction,
)

load_dotenv()
NETWORK = os.getenv("NETWORK", "testnet").lower()
OPERATOR_ID = os.getenv("OPERATOR_ID", "")
OPERATOR_KEY = os.getenv("OPERATOR_KEY", "")


def setup_client() -> Client:
    """Initialize the client using operator credentials from .env."""
    try:
        network = Network(NETWORK)
        client = Client(network)

        operator_id = AccountId.from_string(OPERATOR_ID)
        operator_key = PrivateKey.from_string(OPERATOR_KEY)

        client.set_operator(operator_id, operator_key)

        print(f"Connected to Hedera {NETWORK} as {operator_id}")
        return client

    except Exception:
        print("❌ Error: Could not initialize client. Check your .env file.")
        sys.exit(1)


def create_and_freeze_transaction(client: Client, sender: AccountId, receiver: AccountId):
    """Create and freeze a simple HBAR transfer transaction."""
    tx = (
        TransferTransaction()
        .add_hbar_transfer(sender, -100_000_000)  # -1 HBAR
        .add_hbar_transfer(receiver, 100_000_000)  # +1 HBAR
        .set_transaction_memo("Transaction bytes example")
    )

    tx.freeze_with(client)
    return tx


def serialize_transaction(transaction: Transaction) -> bytes:
    """Serialize transaction to bytes."""
    return transaction.to_bytes()


def deserialize_transaction(bytes_data: bytes) -> Transaction:
    """Restore a transaction from its byte representation."""
    return Transaction.from_bytes(bytes_data)


def main():
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    receiver_id = AccountId.from_string("0.0.3")

    print("\nSTEP 1 — Creating and freezing transaction...")
    tx = create_and_freeze_transaction(client, operator_id, receiver_id)
    print(f"Transaction ID: {tx.transaction_id}")

    print("\nSTEP 2 — Serializing transaction...")
    tx_bytes = serialize_transaction(tx)
    print(f"Serialized size: {len(tx_bytes)} bytes")
    print(f"Preview (hex): {tx_bytes[:40].hex()}")

    print("\nSTEP 3 — Deserializing transaction...")
    restored_tx = deserialize_transaction(tx_bytes)
    print(f"Restored ID: {restored_tx.transaction_id}")
    print(f"Memo: {restored_tx.memo}")

    print("\nSTEP 4 — Signing restored transaction...")
    restored_tx.sign(operator_key)
    print("Signed successfully.")

    print("\nSTEP 5 — Verifying round-trip...")
    original_signed_bytes = tx.sign(operator_key).to_bytes()
    restored_signed_bytes = restored_tx.to_bytes()

    if original_signed_bytes == restored_signed_bytes:
        print("✅ Round-trip serialization successful.")
    else:
        print("❌ Round-trip mismatch!")

    print("\nExample completed.")


if __name__ == "__main__":
    main()
