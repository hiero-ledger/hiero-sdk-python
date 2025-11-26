# MaxAttemptsError

## Overview

`MaxAttemptsError` is an exception that occurs when the SDK has exhausted all retry attempts to communicate with a Hedera network node. This error represents transient network issues or node unavailability rather than transaction logic errors.

## When It Occurs

`MaxAttemptsError` is raised when:
- A node repeatedly fails to respond to requests
- Network connectivity issues prevent communication with a node
- The node is temporarily unavailable or overloaded
- Multiple retry attempts have all failed

## Error Attributes

The `MaxAttemptsError` exception provides the following attributes:

- **`message`** (str): The error message explaining why the maximum attempts were reached
- **`node_id`** (str): The ID of the node that was being contacted when the max attempts were reached
- **`last_error`** (Exception): The last error that occurred during the final attempt

## Error Handling Context

Understanding the different stages of failure is crucial for proper error handling:

1. **Precheck Errors** (`PrecheckError`): Failures before transaction submission (e.g., insufficient balance, invalid signature)
2. **MaxAttemptsError**: Network/node retry failures during communication
3. **Receipt Status Errors** (`ReceiptStatusError`): Failures after consensus (e.g., smart contract revert)

Many developers assume that if `execute()` doesn't throw, the transaction succeeded. These exceptions explicitly show different stages of failure.

## Example Usage

```python
from hiero_sdk_python import Client, TransferTransaction
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError, ReceiptStatusError

# Create client and transaction
client = Client.forTestnet()
transaction = TransferTransaction()
    .addHbarTransfer(sender_account, -1000)
    .addHbarTransfer(receiver_account, 1000)

try:
    # Execute the transaction
    receipt = transaction.execute(client)
    print("Transaction executed successfully")
    
except PrecheckError as e:
    # Handle precheck failures (before submission)
    print(f"Precheck failed: {e.message}")
    print(f"Status: {e.status}")
    
except MaxAttemptsError as e:
    # Handle network/node retry failures
    print(f"Max attempts reached on node {e.node_id}: {e.message}")
    if e.last_error:
        print(f"Last error: {e.last_error}")
    
    # Common recovery strategies:
    # 1. Retry with a different node
    # 2. Wait and retry the same node
    # 3. Check network connectivity
    
except ReceiptStatusError as e:
    # Handle post-consensus failures
    print(f"Transaction failed after consensus: {e.message}")
    print(f"Status: {e.status}")
```

## Recovery Strategies

When encountering a `MaxAttemptsError`, consider these approaches:

### 1. Retry with Different Node
```python
try:
    receipt = transaction.execute(client)
except MaxAttemptsError as e:
    # Switch to a different node and retry
    client.setNetwork([{"node2.hedera.com:50211": "0.0.2"}])
    receipt = transaction.execute(client)
```

### 2. Exponential Backoff
```python
import time

def execute_with_retry(transaction, client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return transaction.execute(client)
        except MaxAttemptsError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1, 2, 4 seconds
            time.sleep(wait_time)
```

### 3. Node Health Check
```python
try:
    receipt = transaction.execute(client)
except MaxAttemptsError as e:
    print(f"Node {e.node_id} appears unhealthy")
    # Implement node health monitoring
    # Consider removing the node from rotation temporarily
```

## Best Practices

1. **Always catch MaxAttemptsError separately** from other exceptions to implement appropriate retry logic
2. **Log the node_id** to identify problematic nodes in your network
3. **Implement circuit breakers** to temporarily skip consistently failing nodes
4. **Use exponential backoff** when retrying to avoid overwhelming the network
5. **Monitor last_error** to understand the root cause of failures

## Related Documentation

- [Receipt Status Error](receipt_status_error.md) - Understanding post-consensus failures
- [Receipts](receipts.md) - Working with transaction receipts
- [Error Handling Guide](../common_issues.md) - General error handling strategies
