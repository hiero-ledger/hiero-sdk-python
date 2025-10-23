# Transaction Bytes Feature

## Overview

This feature adds support for freezing transactions and converting them to bytes instead of executing them immediately. This matches the functionality available in the TypeScript SDK and addresses feature request [#481](https://github.com/hashgraph/hedera-sdk-js/issues/481).

## Motivation

The Python SDK previously only supported executing transactions directly. However, there are several use cases where you need to:

1. **Serialize transactions for later execution** - Store transaction bytes in a database or file system
2. **Transmit transactions** - Send transaction bytes over a network to be executed elsewhere
3. **External signing** - Prepare transaction bytes for signing by external services (HSMs, hardware wallets, etc.)
4. **Batch processing** - Prepare multiple transactions and execute them in batches
5. **Offline signing** - Create and sign transactions on an offline machine

## New Methods

### `Transaction.freeze()`

Freezes the transaction by building the transaction body and setting necessary IDs.

**Requirements:**
- `transaction_id` must be set before calling
- `node_account_id` must be set before calling

**Returns:** `Transaction` (self) for method chaining

**Raises:** `ValueError` if required IDs are not set

**Example:**
```python
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId

transaction = (
    TransferTransaction()
    .add_hbar_transfer(AccountId.from_string("0.0.1234"), -100_000_000)
    .add_hbar_transfer(AccountId.from_string("0.0.5678"), 100_000_000)
)

# Set required IDs manually
transaction.transaction_id = TransactionId.generate(AccountId.from_string("0.0.1234"))
transaction.node_account_id = AccountId.from_string("0.0.3")

# Freeze the transaction
transaction.freeze()
```

### `Transaction.freeze_with(client)`

Freezes the transaction using a client to automatically set transaction ID and node account IDs.

**Parameters:**
- `client` (Client): The client instance to use for setting defaults

**Returns:** `Transaction` (self) for method chaining

**Example:**
```python
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.account.account_id import AccountId

client = Client.for_testnet()
client.set_operator(operator_id, operator_key)

transaction = (
    TransferTransaction()
    .add_hbar_transfer(client.operator_account_id, -100_000_000)
    .add_hbar_transfer(AccountId.from_string("0.0.5678"), 100_000_000)
)

# Freeze with client (automatically sets transaction ID and node IDs)
transaction.freeze_with(client)
```

### `Transaction.to_bytes()`

Serializes the frozen transaction into its protobuf-encoded byte representation.

**Requirements:**
- Transaction must be frozen before calling

**Returns:** `bytes` - The protobuf-encoded transaction bytes

**Raises:** `Exception` if the transaction has not been frozen yet

**Example:**
```python
# After freezing and signing
transaction.freeze_with(client)
transaction.sign(private_key)

# Get the transaction bytes
transaction_bytes = transaction.to_bytes()

# Now you can:
# - Store the bytes in a database
# - Send them over a network
# - Save them to a file
```

### `Transaction.from_bytes(transaction_bytes)` (Static Method)

**Status:** Placeholder implementation - raises `NotImplementedError`

Deserializes a transaction from its protobuf-encoded byte representation.

**Parameters:**
- `transaction_bytes` (bytes): The protobuf-encoded transaction bytes

**Returns:** `Transaction` - A reconstructed transaction instance

**Raises:** 
- `ValueError` if the bytes cannot be parsed as a valid transaction
- `NotImplementedError` - Full implementation requires transaction type detection and reconstruction

**Note:** This method is a placeholder for future implementation. Full implementation requires:
1. Detecting the transaction type from the transaction body
2. Creating the appropriate transaction subclass instance
3. Populating all fields from the protobuf
4. Restoring signatures from the signature map

## Usage Examples

### Basic Workflow

```python
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

# Setup client
client = Client.for_testnet()
client.set_operator(operator_id, operator_key)

# Create transaction
transaction = (
    TransferTransaction()
    .add_hbar_transfer(client.operator_account_id, -100_000_000)
    .add_hbar_transfer(AccountId.from_string("0.0.5678"), 100_000_000)
    .set_transaction_memo("Payment for services")
)

# Freeze the transaction
transaction.freeze_with(client)

# Sign the transaction
transaction.sign(client.operator_private_key)

# Get the transaction bytes
transaction_bytes = transaction.to_bytes()

# Store or transmit the bytes
print(f"Transaction bytes length: {len(transaction_bytes)}")
print(f"First 50 bytes (hex): {transaction_bytes[:50].hex()}")
```

### Manual Freeze (Without Client)

```python
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

# Create transaction
transaction = (
    TransferTransaction()
    .add_hbar_transfer(AccountId.from_string("0.0.1234"), -100_000_000)
    .add_hbar_transfer(AccountId.from_string("0.0.5678"), 100_000_000)
)

# Manually set required IDs
transaction.transaction_id = TransactionId.generate(AccountId.from_string("0.0.1234"))
transaction.node_account_id = AccountId.from_string("0.0.3")

# Freeze without client
transaction.freeze()

# Sign
private_key = PrivateKey.from_string("your_private_key_here")
transaction.sign(private_key)

# Get bytes
transaction_bytes = transaction.to_bytes()
```

### Storing Transaction Bytes

```python
import json
import base64

# After getting transaction bytes
transaction_bytes = transaction.to_bytes()

# Store in a file
with open("transaction.bin", "wb") as f:
    f.write(transaction_bytes)

# Or store as base64 in JSON
transaction_data = {
    "transaction_id": str(transaction.transaction_id),
    "transaction_bytes": base64.b64encode(transaction_bytes).decode('utf-8'),
    "timestamp": "2024-01-01T00:00:00Z"
}

with open("transaction.json", "w") as f:
    json.dump(transaction_data, f)
```

## Comparison with TypeScript SDK

The Python SDK implementation matches the TypeScript SDK's API:

| Feature | TypeScript SDK | Python SDK | Status |
|---------|---------------|------------|--------|
| `freeze()` | ✅ | ✅ | Implemented |
| `freezeWith(client)` | ✅ | ✅ | Implemented |
| `toBytes()` | ✅ | ✅ | Implemented |
| `fromBytes(bytes)` | ✅ | ⚠️ | Placeholder (NotImplementedError) |

## Testing

Comprehensive unit tests are available in `tests/unit/test_transaction_freeze_and_bytes.py`:

```bash
# Run the tests
python -m pytest tests/unit/test_transaction_freeze_and_bytes.py -v
```

Tests cover:
- ✅ Freezing without transaction ID (error case)
- ✅ Freezing without node account ID (error case)
- ✅ Successful freeze with valid parameters
- ✅ Idempotent freeze operations
- ✅ to_bytes() requires frozen transaction
- ✅ to_bytes() returns bytes
- ✅ Consistent output from to_bytes()
- ✅ Cannot modify transaction after freeze
- ✅ from_bytes() error handling
- ✅ Complete freeze -> sign -> to_bytes workflow

## Example Script

A complete example is available in `examples/transaction_bytes_example.py`:

```bash
# Run the example
python examples/transaction_bytes_example.py
```

## Future Enhancements

1. **Complete `from_bytes()` implementation** - Full deserialization support
2. **Transaction type detection** - Automatically detect transaction type from bytes
3. **Batch operations** - Helper methods for batch freeze/sign operations
4. **Transaction templates** - Save and reuse transaction templates

## Related Issues

- Feature Request: [#481](https://github.com/hashgraph/hedera-sdk-js/issues/481) - Support returning transaction bytes instead of executing the transaction

## Migration Guide

### Before (Execute Only)

```python
# Old approach - can only execute immediately
transaction = (
    TransferTransaction()
    .add_hbar_transfer(sender, -amount)
    .add_hbar_transfer(receiver, amount)
)

receipt = transaction.execute(client)
```

### After (Freeze and Get Bytes)

```python
# New approach - can freeze, sign, and get bytes
transaction = (
    TransferTransaction()
    .add_hbar_transfer(sender, -amount)
    .add_hbar_transfer(receiver, amount)
)

# Freeze and sign
transaction.freeze_with(client)
transaction.sign(private_key)

# Get bytes for storage/transmission
transaction_bytes = transaction.to_bytes()

# Execute later or elsewhere
# (when from_bytes() is fully implemented)
```

## Notes

- Freezing a transaction makes it immutable - no further modifications are allowed
- The `freeze()` method requires manual setup of transaction ID and node account ID
- The `freeze_with(client)` method is more convenient as it uses the client's configuration
- Transaction bytes are in protobuf format and can be transmitted or stored
- The `from_bytes()` method is currently a placeholder and will be implemented in a future update
