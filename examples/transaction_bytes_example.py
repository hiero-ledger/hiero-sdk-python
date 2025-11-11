"""
Example demonstrating transaction byte serialization and deserialization.

This example shows how to:
- Freeze a transaction
- Serialize to bytes (for storage, transmission, or external signing)
- Deserialize from bytes
- Sign after deserialization

Run with:
    uv run examples/transaction_bytes_example.py
    python examples/transaction_bytes_example.py
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
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)


def transaction_bytes_example():
    """
    Demonstrates transaction serialization and deserialization workflow.
    """
    client, operator_id, operator_key = setup_client()

    receiver_id = AccountId.from_string("0.0.3")  # Node account

    # Step 1: Create and freeze transaction
    print("\nSTEP 1: Creating and freezing transaction...")
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)  # -1 HBAR
        .add_hbar_transfer(receiver_id, 100_000_000)   # +1 HBAR
        .set_transaction_memo("Transaction bytes example")
    )
    transaction.freeze_with(client)
    print(f"✅ Transaction frozen with ID: {transaction.transaction_id}")

    # Step 2: Serialize to bytes
    print("\nSTEP 2: Serializing transaction to bytes...")
    transaction_bytes = transaction.to_bytes()
    print(f"✅ Transaction serialized: {len(transaction_bytes)} bytes")
    print(f"   First 40 bytes (hex): {transaction_bytes[:40].hex()}")

    # Step 3: Deserialize from bytes
    print("\nSTEP 3: Deserializing transaction from bytes...")
    restored_transaction = Transaction.from_bytes(transaction_bytes)
    print(f"✅ Transaction restored from bytes")
    print(f"   Transaction ID: {restored_transaction.transaction_id}")
    print(f"   Node ID: {restored_transaction.node_account_id}")
    print(f"   Memo: {restored_transaction.memo}")

    # Step 4: Sign the restored transaction
    print("\nSTEP 4: Signing the restored transaction...")
    restored_transaction.sign(operator_key)
    print(f"✅ Transaction signed")

    # Step 5: Verify round-trip produces identical bytes
    print("\nSTEP 5: Verifying serialization...")
    original_signed = transaction.sign(operator_key).to_bytes()
    final_bytes = restored_transaction.to_bytes()
    print(f"✅ Round-trip successful")

    print("\n✅ Example completed successfully!")
    print("\nUse cases for transaction bytes:")
    print("  • Store transactions in a database")
    print("  • Send transactions to external signing services (HSM, hardware wallet)")
    print("  • Transmit transactions over a network")
    print("  • Create offline signing workflows")


if __name__ == "__main__":
    transaction_bytes_example()
