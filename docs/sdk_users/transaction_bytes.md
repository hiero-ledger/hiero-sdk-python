# Transaction Bytes Serialization

## Overview

Support for freezing transactions and converting them to bytes instead of executing immediately. This enables offline signing, external signing services, and transaction storage/transmission.

## New Methods

### `Transaction.freeze()`

Freezes a transaction with manually set IDs.

**Requirements:**
- `transaction_id` must be set
- `node_account_id` must be set

**Returns:** `Transaction` (self) for method chaining

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

### `Transaction.to_bytes()`

Serializes a frozen transaction to protobuf bytes.

**Requirements:** Transaction must be frozen

**Returns:** `bytes`

**Example:**
```python
transaction.freeze_with(client)
transaction.sign(private_key)
transaction_bytes = transaction.to_bytes()
```

### `Transaction.from_bytes(transaction_bytes)`

**Status:** Placeholder - raises `NotImplementedError`

Deserializes transaction from bytes (future implementation).

## Usage

### With Client
```python
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

client = Client.for_testnet()
client.set_operator(operator_id, operator_key)

transaction = TransferTransaction().add_hbar_transfer(...)
transaction.freeze_with(client)
transaction.sign(client.operator_private_key)
transaction_bytes = transaction.to_bytes()
```

### Without Client (Manual)
```python
transaction = TransferTransaction().add_hbar_transfer(...)
transaction.transaction_id = TransactionId.generate(account_id)
transaction.node_account_id = node_id
transaction.freeze()
transaction.sign(private_key)
transaction_bytes = transaction.to_bytes()
```

## Use Cases

- Offline transaction signing
- External signing services (HSMs, hardware wallets)
- Transaction storage and transmission
- Batch processing

## Example

See `examples/transaction_bytes_example.py` for a complete working example.
