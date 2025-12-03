# Understanding Transaction Receipts

Every transaction you submit to the Hedera network—whether it creates a token, transfers HBAR, or deletes an account—produces a **Receipt**.

This guide explains what a receipt is, why you must fetch it, and how to inspect it using the Python SDK.

## What Is a Transaction Receipt?

A transaction receipt is the network’s official confirmation of the transaction's final outcome. It tells you:

1.  **Status:** Whether the transaction reached consensus and succeeded (`SUCCESS`) or failed.
2.  **Created Objects:** If you created something (like a Token or Account), the IDs are stored here.
3.  **Consensus Timestamp:** The exact moment the network agreed the transaction happened.

### ⚠️ Why You Must Check the Receipt

When you run `transaction.execute(client)`, the SDK submits the transaction to a node. If the node accepts it, your script continues. **However, this does not mean the transaction succeeded.**

Without checking the receipt:

- A token might not have been created.
- A transfer might have failed due to insufficient balance.
- **Your script could silently fail** while appearing to work.

## 🛠️ How to Get a Receipt in Python

In the Hiero Python SDK, the `execute()` method resolves to the transaction receipt. You should immediately check the `.status` property.

```python
import sys
from hiero_sdk_python import TokenAssociateTransaction, ResponseCode

# 1. Execute the transaction
receipt = (
    TokenAssociateTransaction()
    .set_account_id(account_id)
    .add_token_id(token_id)
    .freeze_with(client)
    .sign(account_private_key)
    .execute(client)
)

# 2. Check the status
if receipt.status != ResponseCode.SUCCESS:
    # The transaction failed (e.g., wrong key, account full, etc.)
    print(f"Token association failed with status: {ResponseCode(receipt.status).name}")
    sys.exit(1)
else:
    print("Token associated successfully!")
```

## 🔍 Extracting Information from a Receipt

Receipts contain specific fields depending on the type of transaction you executed.

| Transaction Type   | Key Receipt Field    | Description                                           |
| :----------------- | :------------------- | :---------------------------------------------------- |
| **Token Create**   | `receipt.token_id`   | The ID of the newly created token (e.g., `0.0.12345`) |
| **Account Create** | `receipt.account_id` | The ID of the new account                             |
| **Topic Create**   | `receipt.topic_id`   | The ID of the new consensus topic                     |
| **File Create**    | `receipt.file_id`    | The ID of the uploaded file                           |

### Example: Getting a New Token ID

When creating a token, you need the receipt to find out what your new Token ID is so you can use it later.

```python
from hiero_sdk_python import TokenCreateTransaction, ResponseCode

# 1. Create the transaction
create_tx = (
    TokenCreateTransaction()
    .set_token_name("Example Token")
    .set_symbol("EXT")
    .set_initial_supply(1000)
    .set_treasury_account_id(operator_id)
    .freeze_with(client)
    .sign(operator_key)
)

# 2. Execute and get receipt
receipt = create_tx.execute(client)

# 3. Validate Success
if receipt.status != ResponseCode.SUCCESS:
    print(f"Token creation failed: {ResponseCode(receipt.status).name}")
    sys.exit(1)

# 4. Extract the Token ID
token_id = receipt.token_id
print(f"🎉 Created new token with ID: {token_id}")
```

## Summary

1.  **Always check the status:** `if receipt.status != ResponseCode.SUCCESS`.
2.  **Use the receipt for IDs:** Retrieve `token_id` or `account_id` from the receipt object after a successful creation.
3.  **Handle errors:** Never assume a transaction worked just because the code didn't crash during execution.
