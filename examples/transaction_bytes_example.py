"""
Example demonstrating how to freeze a transaction and get its bytes
instead of executing it immediately.

This example shows:
1. Creating a transaction
2. Freezing it with freeze_with(client)
3. Signing it
4. Getting the transaction bytes using to_bytes()
5. The bytes can be stored, transmitted, or used later
"""

import os
from dotenv import load_dotenv

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


def setup_client():
    """
    Sets up and returns a Hedera client configured with operator credentials.
    
    Returns:
        Client: Configured Hedera client instance
    """
    load_dotenv()
    
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    
    client = Client.for_testnet()
    client.set_operator(operator_id, operator_key)
    
    return client


def create_and_freeze_transaction(client):
    """
    Creates a transfer transaction, freezes it, and returns the transaction bytes.
    
    Args:
        client (Client): The Hedera client instance
        
    Returns:
        tuple: (transaction_bytes, transaction_id)
    """
    print("\n📝 Creating a transfer transaction...")
    
    # Create a simple HBAR transfer transaction
    # Transfer 1 HBAR from operator to another account
    receiver_id = AccountId.from_string("0.0.3")  # Using a well-known account
    
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(client.operator_account_id, -100_000_000)  # -1 HBAR
        .add_hbar_transfer(receiver_id, 100_000_000)  # +1 HBAR
        .set_transaction_memo("Transaction bytes example")
    )
    
    print(f"✅ Transaction created: Transfer 1 HBAR from {client.operator_account_id} to {receiver_id}")
    
    # Freeze the transaction with the client
    # This prepares the transaction for signing and serialization
    print("\n🧊 Freezing transaction...")
    transaction.freeze_with(client)
    print("✅ Transaction frozen")
    
    # Sign the transaction
    print("\n✍️  Signing transaction...")
    transaction.sign(client.operator_private_key)
    print("✅ Transaction signed")
    
    # Get the transaction bytes
    print("\n📦 Converting transaction to bytes...")
    transaction_bytes = transaction.to_bytes()
    print(f"✅ Transaction serialized to {len(transaction_bytes)} bytes")
    
    return transaction_bytes, transaction.transaction_id


def demonstrate_transaction_bytes():
    """
    Main function demonstrating the transaction bytes feature.
    """
    print("=" * 70)
    print("🚀 Transaction Bytes Example")
    print("=" * 70)
    print("\nThis example demonstrates how to:")
    print("1. Create a transaction")
    print("2. Freeze it (prepare for signing)")
    print("3. Sign it")
    print("4. Get the transaction bytes")
    print("\nThe bytes can be:")
    print("- Stored for later execution")
    print("- Transmitted to another system")
    print("- Used with external signing services")
    print("=" * 70)
    
    # Setup client
    print("\n🔧 Setting up client...")
    client = setup_client()
    print(f"✅ Client configured for {client.network.network}")
    print(f"✅ Operator: {client.operator_account_id}")
    
    # Create and freeze transaction
    transaction_bytes, transaction_id = create_and_freeze_transaction(client)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 Results")
    print("=" * 70)
    print(f"Transaction ID: {transaction_id}")
    print(f"Transaction bytes length: {len(transaction_bytes)} bytes")
    print(f"First 50 bytes (hex): {transaction_bytes[:50].hex()}")
    print("\n💡 These bytes represent a fully signed transaction that can be:")
    print("   - Stored in a database")
    print("   - Sent over the network")
    print("   - Executed later by calling Transaction.from_bytes() (when implemented)")
    print("   - Submitted to the network using a different client")
    
    print("\n" + "=" * 70)
    print("✅ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_transaction_bytes()
