"""
Test transaction serialization with multi-party signing workflow.

This example demonstrates:
1. Creating a transaction and freezing it
2. Serializing to bytes
3. Deserializing from bytes
4. Signing by multiple parties
5. Executing the transaction

Usage:
    uv run examples/transaction_serialization.py
    python examples/transaction_serialization.py
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
    Hbar,
    CryptoGetAccountBalanceQuery
)

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))
    
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)


def main():
    """
    Demonstrates multi-party signing using transaction serialization.
    
    Workflow:
    1. Party A creates and freezes a transaction
    2. Party A serializes it to bytes
    3. Party A sends bytes to Party B (simulated here)
    4. Party B deserializes from bytes
    5. Party B signs the transaction
    6. Party B executes the transaction
    """
    
    # Setup
    client, operator_id, operator_key = setup_client()
    
    print("\n" + "="*60)
    print("MULTI-PARTY SIGNING WORKFLOW USING TRANSACTION SERIALIZATION")
    print("="*60)
    
    # ========================================
    # STEP 1: Party A creates the transaction
    # ========================================
    print("\n📝 STEP 1: Party A creates and freezes transaction")
    print("-" * 60)
    
    # Create a second account to receive funds (simulating Party B)
    party_b_key = PrivateKey.generate()
    party_b_id = AccountId(0, 0, 1002)  # Using a known test account
    
    amount_to_transfer = Hbar(1)
    
    print(f"Creating transfer of {amount_to_transfer} from {operator_id} to {party_b_id}")
    
    # Party A creates and freezes the transaction
    tx = TransferTransaction()
    tx.add_hbar_transfer(operator_id, -amount_to_transfer.to_tinybars())
    tx.add_hbar_transfer(party_b_id, amount_to_transfer.to_tinybars())
    tx.set_transaction_memo("Multi-party signed transaction")
    tx.freeze_with(client)
    
    print(f"✅ Transaction created with ID: {tx.transaction_id}")
    print(f"   Transaction memo: {tx.memo}")
    print(f"   Frozen for {len(tx._transaction_body_bytes)} nodes")
    
    # ========================================
    # STEP 2: Serialize to bytes
    # ========================================
    print("\n📦 STEP 2: Party A serializes transaction to bytes")
    print("-" * 60)
    
    tx_bytes = tx.to_bytes()
    print(f"✅ Serialized to {len(tx_bytes)} bytes")
    print(f"   First 32 bytes (hex): {tx_bytes[:32].hex()}")
    
    # Optional: Test TransactionList directly
    try:
        tx_list = tx.to_transaction_list()
        print(f"   TransactionList contains {len(tx_list)} transactions")
        print(f"   Nodes: {tx_list.get_node_account_ids()}")
    except Exception as e:
        print(f"   Note: TransactionList not yet implemented ({e})")
    
    # ========================================
    # STEP 3: Simulate sending bytes
    # ========================================
    print("\n📨 STEP 3: Party A sends bytes to Party B")
    print("-" * 60)
    print("   (In real scenario: send via HTTP, gRPC, file, etc.)")
    print(f"   Bytes size: {len(tx_bytes)} bytes")
    
    # ========================================
    # STEP 4: Party B deserializes
    # ========================================
    print("\n📂 STEP 4: Party B receives and deserializes bytes")
    print("-" * 60)
    
    try:
        tx_received = Transaction.from_bytes(tx_bytes)
        print(f"✅ Successfully deserialized transaction")
        print(f"   Transaction type: {type(tx_received).__name__}")
        print(f"   Transaction ID: {tx_received.transaction_id}")
        print(f"   Transaction memo: {tx_received.memo}")
        print(f"   Number of node transactions: {len(tx_received._transaction_body_bytes)}")
        
        # Verify it's a TransferTransaction
        if isinstance(tx_received, TransferTransaction):
            print(f"   HBAR transfers: {len(tx_received.hbar_transfers)}")
            for transfer in tx_received.hbar_transfers:
                print(f"     - {transfer.account_id}: {transfer.amount} tinybars")
        
    except Exception as e:
        print(f"❌ Deserialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ========================================
    # STEP 5: Verify signatures
    # ========================================
    print("\n🔐 STEP 5: Check existing signatures")
    print("-" * 60)
    
    is_signed_by_operator = tx_received.is_signed_by(operator_key.public_key())
    print(f"   Signed by operator: {is_signed_by_operator}")
    
    if not is_signed_by_operator:
        print("   Transaction needs operator signature")
    
    # ========================================
    # STEP 6: Party B signs the transaction
    # ========================================
    print("\n✍️  STEP 6: Party B adds their signature")
    print("-" * 60)
    
    # In this example, we'll sign with the operator key
    # In a real multi-party scenario, Party B would have their own key
    try:
        tx_received.sign(operator_key)
        print(f"✅ Transaction signed by operator")
        
        # Verify signature was added
        is_now_signed = tx_received.is_signed_by(operator_key.public_key())
        print(f"   Verified signature: {is_now_signed}")
        
    except Exception as e:
        print(f"❌ Signing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ========================================
    # STEP 7: Execute the transaction
    # ========================================
    print("\n🚀 STEP 7: Execute the signed transaction")
    print("-" * 60)
    
    try:
        # Check balance before
        print(f"Querying balance before transfer...")
        balance_before = CryptoGetAccountBalanceQuery(account_id=party_b_id).execute(client).hbars
        print(f"   Party B balance before: {balance_before}")
        
        # Execute
        print("Executing transaction...")
        receipt = tx_received.execute(client)
        
        print(f"✅ Transaction executed successfully!")
        print(f"   Status: {receipt.status}")
        print(f"   Transaction ID: {receipt.transaction_id}")
        
        # Check balance after
        print(f"Querying balance after transfer...")
        balance_after = CryptoGetAccountBalanceQuery(account_id=party_b_id).execute(client).hbars
        print(f"   Party B balance after: {balance_after}")
        print(f"   Change: +{balance_after.to_tinybars() - balance_before.to_tinybars()} tinybars")
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ========================================
    # STEP 8: Round-trip verification
    # ========================================
    print("\n🔄 STEP 8: Round-trip verification")
    print("-" * 60)
    
    try:
        # Serialize the signed transaction
        tx_bytes_signed = tx_received.to_bytes()
        print(f"✅ Serialized signed transaction: {len(tx_bytes_signed)} bytes")
        
        # Deserialize again
        tx_final = Transaction.from_bytes(tx_bytes_signed)
        print(f"✅ Deserialized again successfully")
        
        # Verify signature is preserved
        is_still_signed = tx_final.is_signed_by(operator_key.public_key())
        print(f"   Signature preserved: {is_still_signed}")
        
        # Verify transaction details match
        matches = (
            tx_final.transaction_id == tx_received.transaction_id and
            tx_final.memo == tx_received.memo
        )
        print(f"   Transaction details match: {matches}")
        
    except Exception as e:
        print(f"❌ Round-trip verification failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ MULTI-PARTY SIGNING WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. Transactions can be serialized to bytes after freezing")
    print("2. Bytes can be sent between parties (HTTP, gRPC, file, etc.)")
    print("3. Parties can deserialize and add signatures independently")
    print("4. Signatures are preserved through serialization/deserialization")
    print("5. Any party with the complete signed transaction can execute it")


if __name__ == "__main__":
    main()