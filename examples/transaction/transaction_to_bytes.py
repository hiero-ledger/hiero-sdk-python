"""
Example demonstrating transaction byte serialization and deserialization.

This example shows how to:
- Create and freeze a transaction
- Serialize to bytes (for storage, transmission, or signing)
- Deserialize from bytes
- Sign a deserialized transaction

Run with:
  uv run examples/transaction/transaction_to_bytes.py
  python examples/transaction/transaction_to_bytes.py
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

        print(f"Connected to network '{NETWORK}' as {operator_id}")
        return client

    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        sys.exit(1)


def create_and_freeze_transaction(
    client: Client, sender: AccountId, receiver: AccountId
):
    """Create and freeze a simple HBAR transfer transaction."""
    tx = (
        TransferTransaction()
        .add_hbar_transfer(sender, -100_000_000)  # -1 HBAR
        .add_hbar_transfer(receiver, 100_000_000)  # +1 HBAR
        .set_transaction_memo("Transaction bytes example")
    )

    tx.freeze_with(client)
    # print a concise confirmation for the user
    print(f"✅ Transaction frozen with ID: {tx.transaction_id}")
    return tx


def serialize_transaction(transaction: Transaction) -> bytes:
    """Serialize transaction to bytes."""
    tx_bytes = transaction.to_bytes()
    print(f"✅ Transaction serialized: {len(tx_bytes)} bytes")
    print(f" Preview (first 40 bytes hex): {tx_bytes[:40].hex()}")
    return tx_bytes


def deserialize_transaction(bytes_data: bytes) -> Transaction:
    """Restore a transaction from its byte representation."""
    restored = Transaction.from_bytes(bytes_data)
    print("✅ Transaction restored from bytes")
    print(f" Restored ID: {restored.transaction_id}")
    print(f" Memo: {restored.memo}")
    return restored


def main():
    # Initialize client (exits with message if fails)
    client = setup_client()

    # obtain operator information from the client
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    # receiver example (adjust as needed)
    receiver_id = AccountId.from_string("0.0.3")

    try:
        print("\nSTEP 1 — Creating and freezing transaction...")
        tx = create_and_freeze_transaction(client, operator_id, receiver_id)

        print("\nSTEP 2 — Serializing transaction...")
        tx_bytes = serialize_transaction(tx)

        print("\nSTEP 3 — Deserializing transaction...")
        restored_tx = deserialize_transaction(tx_bytes)

        print("\nSTEP 4 — Signing restored transaction...")
        restored_tx.sign(operator_key)
        print("✅ Signed restored transaction successfully.")

        print("\nSTEP 5 — Verifying round-trip (signed bytes comparison)...")
        # Sign the original transaction as well to compare the signed bytes
        original_signed_bytes = tx.sign(operator_key).to_bytes()
        restored_signed_bytes = restored_tx.to_bytes()

        if original_signed_bytes == restored_signed_bytes:
            print("✅ Round-trip serialization successful.")
        else:
            print("❌ Round-trip mismatch!")

        print("\nExample completed.")

    except Exception as e:
        print(f"❌ Error in example flow: {e}")


if __name__ == "__main__":
    main()
