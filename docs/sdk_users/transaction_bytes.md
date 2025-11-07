# Transaction Bytes Serialization

## Overview

Support for freezing transactions and converting them to bytes instead of executing immediately. This enables offline signing, external signing services (HSMs, hardware wallets), and transaction storage/transmission.

## New Methods

### `Transaction.freeze()`

Freezes a transaction with manually set IDs for **single-node execution**.

**Requirements:**
- `transaction_id` must be set
- `node_account_id` must be set

**Returns:** `Transaction` (self) for method chaining

**⚠️ Important Limitation:**
This method only builds the transaction body for the single node specified. If the network needs to retry with a different node, the transaction will fail. For production use, prefer `freeze_with(client)`.

**Example:**
```python
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId

transaction = TransferTransaction().add_hbar_transfer(...)
transaction.transaction_id = TransactionId.generate(AccountId.from_string("0.0.1234"))
transaction.node_account_id = AccountId.from_string("0.0.3")
transaction.freeze()
```

### `Transaction.freeze_with(client)`

Freezes a transaction using client for **multi-node execution with automatic failover**.

**Advantages:**
- Automatically sets transaction_id from client's operator
- Builds transaction bodies for **all nodes** in the network
- Enables automatic node failover if a node is unavailable
- Recommended for production use

**Example:**
```python
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

client = Client.for_testnet()
client.set_operator(operator_id, operator_key)

transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)  # Builds for all network nodes
```

### `Transaction.to_bytes()`

Serializes a frozen transaction to protobuf bytes.

**Requirements:** Transaction must be frozen (with `freeze()` or `freeze_with()`)

**Signing:** Optional - works with both signed and unsigned transactions
- **Unsigned bytes**: Can be sent to external signing services or HSMs
- **Signed bytes**: Ready for submission to the network

**Returns:** `bytes`

**Examples:**

**Unsigned transaction (for external signing):**
```python
transaction.freeze_with(client)
unsigned_bytes = transaction.to_bytes()
# Send unsigned_bytes to HSM or hardware wallet for signing
```

**Signed transaction (ready for submission):**
```python
transaction.freeze_with(client)
transaction.sign(private_key)
signed_bytes = transaction.to_bytes()
# signed_bytes can be stored, transmitted, or submitted to network
```

**Multiple signatures:**
```python
transaction.freeze_with(client)
transaction.sign(key1)
transaction.sign(key2)
transaction.sign(key3)
multi_sig_bytes = transaction.to_bytes()
```

### `Transaction.from_bytes(transaction_bytes)`

Deserializes a transaction from protobuf-encoded bytes.

**Requirements:** The bytes must have been created using `to_bytes()`

**What is restored:**
- Transaction type and all transaction-specific fields
- Common fields (transaction ID, node ID, memo, fee, etc.)
- All signatures (if the transaction was signed)
- Transaction state (frozen)

**Returns:** The appropriate `Transaction` subclass instance (e.g., `TransferTransaction`)

**Examples:**

**Basic round-trip:**
```python
# Serialize
tx = TransferTransaction().add_hbar_transfer(...)
tx.freeze_with(client)
tx_bytes = tx.to_bytes()

# Deserialize
restored_tx = Transaction.from_bytes(tx_bytes)
```

**External signing:**
```python
# System A: Create and serialize unsigned transaction
tx = TransferTransaction().add_hbar_transfer(...)
tx.freeze_with(client)
unsigned_bytes = tx.to_bytes()

# System B: Restore, sign, and serialize
tx = Transaction.from_bytes(unsigned_bytes)
tx.sign(hsm_key)
signed_bytes = tx.to_bytes()

# System A: Restore and execute
final_tx = Transaction.from_bytes(signed_bytes)
receipt = final_tx.execute(client)
```

## Method Comparison

| Feature | `freeze()` | `freeze_with(client)` |
|---------|-----------|----------------------|
| Sets transaction_id | ❌ Manual required | ✅ Automatic |
| Sets node_account_id | ❌ Manual required | ✅ Automatic |
| Builds for single node | ✅ Yes | ❌ No |
| Builds for all nodes | ❌ No | ✅ Yes |
| Supports node failover | ❌ No | ✅ Yes |
| Use for offline signing | ✅ Yes | ✅ Yes |
| Use for execute(client) | ⚠️ Single node only | ✅ Recommended |

## Use Cases

### 1. Offline Transaction Signing

Create transaction bytes on an online system, transfer to an offline system for signing:

```python
# Online system
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.transaction_id = TransactionId.generate(account_id)
transaction.node_account_id = AccountId.from_string("0.0.3")
transaction.freeze()
unsigned_bytes = transaction.to_bytes()

# Transfer unsigned_bytes to offline system...

# Offline system (air-gapped)
tx = Transaction.from_bytes(unsigned_bytes)
tx.sign(offline_private_key)
signed_bytes = tx.to_bytes()

# Transfer signed_bytes back to online system...

# Online system
final_tx = Transaction.from_bytes(signed_bytes)
receipt = final_tx.execute(client)
```

### 2. Hardware Wallet / HSM Integration

```python
# Prepare transaction
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)
unsigned_bytes = transaction.to_bytes()

# Send to HSM for signing
signed_bytes = hsm.sign_transaction(unsigned_bytes)

# Reconstruct and submit to network
tx = Transaction.from_bytes(signed_bytes)
receipt = tx.execute(client)
```

### 3. Transaction Storage

```python
# Create and sign transaction
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)
transaction.sign(private_key)
transaction_bytes = transaction.to_bytes()

# Store in database
database.store("pending_tx_123", transaction_bytes)

# Later, retrieve and execute
stored_bytes = database.get("pending_tx_123")
transaction = Transaction.from_bytes(stored_bytes)
receipt = transaction.execute(client)
```

### 4. Batch Processing

```python
# Create multiple transactions
transactions = []
for payment in payments_list:
    tx = TransferTransaction().add_hbar_transfer(...)
    tx.freeze_with(client)
    transactions.append(tx)

# Sign all at once
for tx in transactions:
    tx.sign(private_key)

# Serialize for batch transmission
batch_bytes = [tx.to_bytes() for tx in transactions]
```

## Common Patterns

### Pattern 1: Immediate Execution (Most Common)

```python
# Don't call freeze manually - execute() does it automatically
client = Client.for_testnet()
client.set_operator(operator_id, operator_key)

receipt = (
    TransferTransaction()
    .add_hbar_transfer(sender, -amount)
    .add_hbar_transfer(receiver, amount)
    .execute(client)  # Automatically freezes and signs
)
```

### Pattern 2: Manual Freeze for Inspection

```python
# Freeze to inspect transaction before signing
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)

# Inspect transaction details
print(f"Transaction ID: {transaction.transaction_id}")
print(f"Transaction fee: {transaction.transaction_fee}")

# Then sign and execute
transaction.sign(client.operator_private_key)
receipt = transaction.execute(client)
```

### Pattern 3: External Signing

```python
# Prepare transaction
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)

# Get bytes for external signing
unsigned_bytes = transaction.to_bytes()

# External system signs the transaction
tx = Transaction.from_bytes(unsigned_bytes)
tx.sign(external_key)
signed_bytes = tx.to_bytes()

# Original system executes the signed transaction
final_tx = Transaction.from_bytes(signed_bytes)
receipt = final_tx.execute(client)
```

## Limitations

1. **`freeze()` single-node limitation**: Only builds for one node, no automatic failover
2. **Signature verification**: No built-in method to verify signatures before submission
3. **Transaction type support**: `from_bytes()` currently only supports `TransferTransaction`. Other transaction types will need to implement the `_from_protobuf()` method to be fully supported

## Migration from Execute-Only Pattern

**Before (execute only):**
```python
receipt = TransferTransaction().add_hbar_transfer(...).execute(client)
```

**After (with bytes serialization):**
```python
tx = TransferTransaction().add_hbar_transfer(...)
tx.freeze_with(client)
tx.sign(client.operator_private_key)
tx_bytes = tx.to_bytes()

# Store, transmit, or inspect tx_bytes as needed

# Then execute
receipt = tx.execute(client)
```

## See Also

- `examples/transaction_bytes_example.py` - Complete working example
- Transaction signing documentation
- Client configuration guide
