# Transaction Lifecycle in the Python SDK

This guide explains the typical lifecycle of executing a transaction using the Hedera Python SDK. Transactions are requests to change the state of the Hedera network, such as creating accounts, transferring HBAR, or minting tokens. Understanding the lifecycle helps you avoid common pitfalls and ensures your transactions succeed.

## Overview

A typical transaction follows this flow:

1. **Construct** the transaction
2. **Freeze** the transaction
3. **Sign** the transaction
4. **Execute** the transaction
5. **Check the receipt**

The order matters because each step builds on the previous one. Skipping or reordering steps can cause errors.

## 1. Construct the Transaction

Start by creating a transaction object and populating it with the necessary data. You can use either Pythonic syntax (constructor arguments) or method chaining (fluent API).

### Pythonic Syntax
```python
from hiero_sdk_python import TokenAssociateTransaction

transaction = TokenAssociateTransaction(
    account_id=account_id,
    token_ids=[token_id]
)
```

### Method Chaining
```python
transaction = (
    TokenAssociateTransaction()
    .set_account_id(account_id)
    .add_token_id(token_id)
)
```

This step collects all information for the transaction body. Fields can still be modified at this point.

## 2. Freeze the Transaction

Freezing finalizes the transaction payload and makes it immutable. It sets the transaction ID, node ID, and builds the protobuf body.

```python
transaction.freeze_with(client)
```

- **Why freeze?** Hedera requires a consistent payload for signing and execution. Freezing prevents accidental changes.
- **When to freeze?** Always before signing. Some transactions auto-freeze during execution, but manual freezing is recommended for clarity.
- **What happens if you don't freeze?** Signing or executing may fail or behave unexpectedly.

## 3. Sign the Transaction

Hedera uses cryptographic signatures for authorization. Sign with the required keys (e.g., operator key, admin keys).

```python
transaction.sign(account_private_key)
```

- **Who signs?** The operator (client account) often signs automatically, but additional keys may be needed (e.g., supply key for minting).
- **Multiple signatures?** Call `.sign()` multiple times if required.
- **Order?** Sign after freezing, as the payload must be finalized.

## 4. Execute the Transaction

Submit the transaction to the Hedera network. This returns a `TransactionResponse` indicating the network received it.

```python
response = transaction.execute(client)
```

- **Does this guarantee success?** No! It only confirms receipt. The network processes it asynchronously.
- **What if you skip signing?** Execution will fail with an authorization error.

## 5. Check the Receipt

Fetch and verify the transaction receipt to confirm processing.

```python
receipt = response.get_receipt(client)

if receipt.status != ResponseCode.SUCCESS:
    print(f"Transaction failed: {ResponseCode(receipt.status).name}")
else:
    print("Transaction successful!")
```

- **Why check?** Receipts provide the final status and any generated IDs (e.g., new account ID).
- **Common statuses:** `SUCCESS`, `INSUFFICIENT_ACCOUNT_BALANCE`, `INVALID_SIGNATURE`.

## Complete Example

Here's a clean example associating a token with an account:

```python
import sys
from hiero_sdk_python import TokenAssociateTransaction, ResponseCode

def associate_token_with_account(client, account_id, account_private_key, token_id):
    """Associate a token with an account."""

    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)          # Lock fields
        .sign(account_private_key)    # Authorize
        .execute(client)              # Submit to Hedera
        .get_receipt(client)          # Fetch result
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Token associated successfully!")
```

For more examples, see `examples/token_grant_kyc.py` or `examples/token_associate.py`.

## Correct vs. Incorrect Order

### Correct
```python
transaction = TokenAssociateTransaction().set_account_id(account_id).freeze_with(client).sign(key).execute(client)
receipt = response.get_receipt(client)
```

### Incorrect (Signing before freezing)
```python
transaction = TokenAssociateTransaction().set_account_id(account_id).sign(key).freeze_with(client)  # Error: Cannot sign unfrozen transaction
```

### Incorrect (Modifying after freezing)
```python
transaction = TokenAssociateTransaction().set_account_id(account_id).freeze_with(client)
transaction.set_account_id(new_id)  # Error: Transaction is immutable
```

## Flow Diagram

```
[Construct] → [Freeze] → [Sign] → [Execute] → [Check Receipt]
     ↓          ↓         ↓         ↓            ↓
  Build data  Finalize  Authorize  Submit     Verify status
```

## Common Pitfalls

- **Forgetting to freeze:** Leads to runtime errors during signing.
- **Wrong signer:** Use the correct key (e.g., supply key for minting).
- **Ignoring receipt:** Always check status; don't assume success.
- **Auto-freeze/sign:** Works for simple transactions but can hide issues in complex ones.
- **Order dependency:** Construct → Freeze → Sign → Execute → Receipt.

For more details, refer to the SDK documentation or community calls on [Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md).