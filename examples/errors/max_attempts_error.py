"""
Example demonstrating MaxAttemptsError handling in Hedera SDK

This example shows how to handle MaxAttemptsError exceptions that occur
when the SDK exhausts retry attempts to communicate with network nodes.
"""

import time
from hiero_sdk_python import Client, TransferTransaction, AccountId, PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError, ReceiptStatusError


def basic_max_attempts_example():
    """
    Basic example of catching MaxAttemptsError
    """
    print("=== Basic MaxAttemptsError Example ===")
    
    # Initialize client
    client = Client.forTestnet()
    
    # Create a simple transfer transaction
    sender = AccountId.fromString("0.0.12345")
    receiver = AccountId.fromString("0.0.67890")
    private_key = PrivateKey.fromString("302e020100300506032b657004220420db484b8284a5c6826c0e07c2d8296fda0b841d4e1dc4b7f308a2db69b043a8c5")
    
    transaction = TransferTransaction()
        .addHbarTransfer(sender, -1000)
        .addHbarTransfer(receiver, 1000)
        .freezeWith(client)
        .sign(private_key)
    
    try:
        receipt = transaction.execute(client)
        print("✅ Transaction executed successfully")
        
    except PrecheckError as e:
        print(f"❌ Precheck failed: {e.message}")
        print(f"   Status: {e.status}")
        
    except MaxAttemptsError as e:
        print(f"❌ Max attempts reached on node {e.node_id}")
        print(f"   Error: {e.message}")
        if e.last_error:
            print(f"   Last error: {type(e.last_error).__name__}: {e.last_error}")
        
        # Example recovery action
        print("   💡 Recovery: Consider retrying with a different node")
        
    except ReceiptStatusError as e:
        print(f"❌ Transaction failed after consensus: {e.message}")
        print(f"   Status: {e.status}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


def retry_with_different_node():
    """
    Example demonstrating retry with a different node when MaxAttemptsError occurs
    """
    print("\n=== Retry with Different Node Example ===")
    
    # Initialize client with multiple nodes
    client = Client.forTestnet()
    
    # Define alternative nodes
    alternative_nodes = [
        {"0.0.3": "35.237.200.180:50211"},
        {"0.0.4": "35.186.191.247:50211"},
        {"0.0.5": "35.192.2.44:50211"}
    ]
    
    sender = AccountId.fromString("0.0.12345")
    receiver = AccountId.fromString("0.0.67890")
    private_key = PrivateKey.fromString("302e020100300506032b657004220420db484b8284a5c6826c0e07c2d8296fda0b841d4e1dc4b7f308a2db69b043a8c5")
    
    transaction = TransferTransaction()
        .addHbarTransfer(sender, -1000)
        .addHbarTransfer(receiver, 1000)
        .freezeWith(client)
        .sign(private_key)
    
    # Try with original node first
    try:
        receipt = transaction.execute(client)
        print("✅ Transaction executed successfully with original node")
        return receipt
        
    except MaxAttemptsError as e:
        print(f"⚠️  Original node {e.node_id} failed after max attempts")
        print(f"   Error: {e.message}")
        
        # Try alternative nodes
        for i, node_map in enumerate(alternative_nodes):
            try:
                print(f"   🔄 Trying alternative node {i+1}...")
                client.setNetwork([node_map])
                receipt = transaction.execute(client)
                print(f"✅ Transaction succeeded with alternative node {i+1}")
                return receipt
                
            except MaxAttemptsError as retry_error:
                print(f"   ❌ Alternative node {i+1} also failed: {retry_error.message}")
                continue
                
        print("❌ All nodes failed. Transaction could not be completed.")
        return None


def exponential_backoff_retry():
    """
    Example demonstrating exponential backoff retry strategy
    """
    print("\n=== Exponential Backoff Retry Example ===")
    
    client = Client.forTestnet()
    
    sender = AccountId.fromString("0.0.12345")
    receiver = AccountId.fromString("0.0.67890")
    private_key = PrivateKey.fromString("302e020100300506032b657004220420db484b8284a5c6826c0e07c2d8296fda0b841d4e1dc4b7f308a2db69b043a8c5")
    
    transaction = TransferTransaction()
        .addHbarTransfer(sender, -1000)
        .addHbarTransfer(receiver, 1000)
        .freezeWith(client)
        .sign(private_key)
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"   📤 Attempt {attempt + 1} of {max_retries}...")
            receipt = transaction.execute(client)
            print(f"✅ Transaction succeeded on attempt {attempt + 1}")
            return receipt
            
        except MaxAttemptsError as e:
            if attempt == max_retries - 1:
                print(f"❌ All {max_retries} attempts failed")
                print(f"   Final error: {e.message}")
                return None
                
            # Calculate wait time: 1s, 2s, 4s for attempts 0, 1, 2
            wait_time = 2 ** attempt
            print(f"   ⏳ Waiting {wait_time} seconds before retry...")
            print(f"   Last error: {e.last_error if e.last_error else 'No specific error'}")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            break
    
    return None


def node_health_monitoring():
    """
    Example showing how to monitor node health based on MaxAttemptsError
    """
    print("\n=== Node Health Monitoring Example ===")
    
    # Simple node health tracking
    node_failures = {}
    
    client = Client.forTestnet()
    
    sender = AccountId.fromString("0.0.12345")
    receiver = AccountId.fromString("0.0.67890")
    private_key = PrivateKey.fromString("302e020100300506032b657004220420db484b8284a5c6826c0e07c2d8296fda0b841d4e1dc4b7f308a2db69b043a8c5")
    
    transaction = TransferTransaction()
        .addHbarTransfer(sender, -1000)
        .addHbarTransfer(receiver, 1000)
        .freezeWith(client)
        .sign(private_key)
    
    try:
        receipt = transaction.execute(client)
        print("✅ Transaction executed successfully")
        
    except MaxAttemptsError as e:
        node_id = e.node_id
        error_msg = e.message
        
        # Track node failures
        if node_id not in node_failures:
            node_failures[node_id] = []
        node_failures[node_id].append({
            'timestamp': time.time(),
            'error': error_msg,
            'last_error': str(e.last_error) if e.last_error else None
        })
        
        print(f"❌ Node {node_id} failure recorded")
        print(f"   Error: {error_msg}")
        print(f"   Total failures for this node: {len(node_failures[node_id])}")
        
        # Simple health check logic
        if len(node_failures[node_id]) >= 3:
            print(f"   🚨 Node {node_id} marked as unhealthy (3+ failures)")
            print("   💡 Consider removing this node from rotation temporarily")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
    
    # Print node health summary
    if node_failures:
        print("\n📊 Node Health Summary:")
        for node_id, failures in node_failures.items():
            print(f"   Node {node_id}: {len(failures)} failures")


def comprehensive_error_handling():
    """
    Comprehensive example showing all error types and their handling
    """
    print("\n=== Comprehensive Error Handling Example ===")
    
    client = Client.forTestnet()
    
    sender = AccountId.fromString("0.0.12345")
    receiver = AccountId.fromString("0.0.67890")
    private_key = PrivateKey.fromString("302e020100300506032b657004220420db484b8284a5c6826c0e07c2d8296fda0b841d4e1dc4b7f308a2db69b043a8c5")
    
    transaction = TransferTransaction()
        .addHbarTransfer(sender, -1000)
        .addHbarTransfer(receiver, 1000)
        .freezeWith(client)
        .sign(private_key)
    
    try:
        receipt = transaction.execute(client)
        print("✅ Transaction executed successfully")
        print(f"   Transaction ID: {receipt.transactionId}")
        
    except PrecheckError as e:
        print("🔍 PRECHECK ERROR (Before submission)")
        print(f"   Status: {e.status}")
        print(f"   Message: {e.message}")
        if e.transaction_id:
            print(f"   Transaction ID: {e.transaction_id}")
        print("   💡 Fix: Check account balance, fees, signatures, etc.")
        
    except MaxAttemptsError as e:
        print("🌐 MAX ATTEMPTS ERROR (Network/Node failure)")
        print(f"   Node ID: {e.node_id}")
        print(f"   Message: {e.message}")
        if e.last_error:
            print(f"   Last error: {type(e.last_error).__name__}: {e.last_error}")
        print("   💡 Fix: Retry with different node, check network, wait and retry")
        
    except ReceiptStatusError as e:
        print("📋 RECEIPT STATUS ERROR (After consensus)")
        print(f"   Status: {e.status}")
        print(f"   Transaction ID: {e.transaction_id}")
        print(f"   Message: {e.message}")
        print("   💡 Fix: Check smart contract logic, account state, etc.")
        
    except Exception as e:
        print("❌ UNEXPECTED ERROR")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        print("   💡 Fix: Check SDK version, network configuration, etc.")


if __name__ == "__main__":
    print("MaxAttemptsError Handling Examples")
    print("=" * 50)
    
    # Run all examples
    basic_max_attempts_example()
    retry_with_different_node()
    exponential_backoff_retry()
    node_health_monitoring()
    comprehensive_error_handling()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nKey Takeaways:")
    print("• MaxAttemptsError indicates network/node issues, not transaction logic errors")
    print("• Always catch MaxAttemptsError separately for proper retry logic")
    print("• Log node_id to identify problematic nodes")
    print("• Implement exponential backoff when retrying")
    print("• Consider circuit breakers for consistently failing nodes")
