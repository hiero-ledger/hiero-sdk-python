# Coding Token Transactions

This guide provides a high-level overview of how token transactions are constructed in the Hiero Python SDK. It is intended for developers adding new transaction types (e.g., `TokenMintTransaction`, `TokenBurnTransaction`) to understand the architectural requirements.

## 1. Inheritance Structure

All token transactions must inherit from the base `Transaction` class.

```python
from hiero_sdk_python.transaction.transaction import Transaction

class TokenAssociateTransaction(Transaction):
    """
    Represents a token associate transaction on the Hedera network.
    """

```

By inheriting from `Transaction`, your new class automatically gains essential functionality:

- **Signing:** `sign(private_key)`
- **Freezing:** `freeze()` and `freeze_with(client)`
- **Execution:** `execute(client)`
- **Fee Calculation:** Handling `transaction_fee` and `max_transaction_fee`
- **ID Management:** `transaction_id`, `node_account_id`

Your job in the subclass is to define **what** data is being sent, while the base class handles **how** it is sent.

## 2. Initialization and Defaults

In the Python SDK, we prefer a flexible initialization pattern. Constructors (`__init__`) should generally default arguments to `None`. This allows users to instantiate an empty transaction and configure it later using setters (Method Chaining).

### Pattern:

```python
def __init__(
    self,
    account_id: Optional[AccountId] = None,
    token_ids: Optional[List[TokenId]] = None
) -> None:
    super().__init__()  # Initialize the base Transaction
    self.account_id = account_id
    self.token_ids = list(token_ids) if token_ids is not None else []

```

- **Why?** It supports both "all-in-one" instantiation and progressive building.
- **Note:** Always call `super().__init__()` to initialize base fields like the signature map and transaction ID.

## 3. Setters and Method Chaining

To provide a "Pythonic" builder interface, every field should have a corresponding setter method. These methods must:

1. Check that the transaction is not frozen (immutable).
2. Return `self` to allow chaining (e.g., `.set_foo().set_bar()`).

### Pattern:

```python
def set_account_id(self, account_id: AccountId) -> "TokenAssociateTransaction":
    """Sets the account ID for the token association transaction."""
    self._require_not_frozen()  # Critical check from base class
    self.account_id = account_id
    return self

```

This feature enables chaining.

For example:

### Standard Usage

```python
tx.set_account_id(account_id)
tx.set_token_id(token_id)
tx.freeze()
tx.execute(client)
```
or
### Method Chaining
```python
tx.set_account_id(account_id).set_token_id(token_id).freeze().execute(client)
```

## 4. Protobuf Conversion

The Hedera network communicates via Protocol Buffers (Protobuf). Your transaction class is responsible for converting its Python fields into a Protobuf message.

This is typically done in three steps:

### Step A: Internal Helper `_build_proto_body()`

Create a helper method that constructs the _specific_ body for your transaction type (e.g., `TokenAssociateTransactionBody`).

```python
def _build_proto_body(self) -> token_associate_pb2.TokenAssociateTransactionBody:
    if not self.account_id or not self.token_ids:
        raise ValueError("Account ID and token IDs must be set.")

    return token_associate_pb2.TokenAssociateTransactionBody(
        account=self.account_id._to_proto(),
        tokens=[token_id._to_proto() for token_id in self.token_ids]
    )

```

### Step B: Implement `build_transaction_body()`

This abstract method from `Transaction` must be implemented. It packages your specific body into the main `TransactionBody`.

```python
def build_transaction_body(self) -> transaction_pb2.TransactionBody:
    # 1. Build your specific proto body
    token_associate_body = self._build_proto_body()

    # 2. Get the base body (contains NodeID, TxID, Fees, Memo)
    transaction_body = self.build_base_transaction_body()

    # 3. Attach your specific body to the main transaction
    transaction_body.tokenAssociate.CopyFrom(token_associate_body)

    return transaction_body

```

### Step C: Implement `build_scheduled_body()`

To support scheduled transactions, you must also implement this method. It is nearly identical to step B but uses `SchedulableTransactionBody`.

```python
def build_scheduled_body(self) -> SchedulableTransactionBody:
    token_associate_body = self._build_proto_body()
    schedulable_body = self.build_base_scheduled_body()
    schedulable_body.tokenAssociate.CopyFrom(token_associate_body)
    return schedulable_body

```

## 5. Network Routing (`_get_method`)

Finally, you must tell the base class which gRPC method to call on the node. This routes the transaction to the correct service (e.g., Token Service vs. Crypto Service).

```python
def _get_method(self, channel: _Channel) -> _Method:
    return _Method(
        transaction_func=channel.token.associateTokens, # The gRPC function
        query_func=None
    )

```

---

## Summary Checklist

When creating a new token transaction, ensure you have:

- [ ] **Inherited** from `Transaction`.
- [ ] **Initialized** fields to `None` in `__init__`.
- [ ] **Implemented Setters** that call `self._require_not_frozen()` and return `self`.
- [ ] **Implemented** `_build_proto_body()` to map Python fields to Protobuf.
- [ ] **Implemented** `build_transaction_body()` to merge your body into the main transaction.
- [ ] **Implemented** `build_scheduled_body()` for scheduling support.
- [ ] **Implemented** `_get_method()` to define the gRPC endpoint.

The base `Transaction` class will handle the heavy lifting of freezing, signing, serialization, and execution.

---
