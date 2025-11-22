# ReceiptStatusError

This guide explains `ReceiptStatusError` in the Hiero SDK, how it differs from other errors, and how to handle it effectively.

## Error Handling Overview

Many developers assume that if `execute()` doesn't throw an exception, the transaction or query succeeded. However, failures can occur at different stages:

1.  **Precheck (Before Submission):**
    *   Occurs if the transaction is malformed or fails initial validation by the node.
    *   The SDK raises a `PrecheckError` (or similar) immediately.
    *   The transaction never reaches consensus.

2.  **Network/Node Retry Failures:**
    *   Occurs if the SDK cannot reach a node or receives transient errors (e.g., `BUSY`).
    *   The SDK automatically retries up to a limit.
    *   If retries are exhausted, a `MaxAttemptsError` or `TimeoutError` is raised.

3.  **Receipt Status Errors (Post-Consensus):**
    *   Occurs **after** the network reaches consensus on the transaction.
    *   The transaction was successfully submitted and processed, but the logic failed (e.g., insufficient funds, token supply full, invalid signature for the specific operation).
    *   This is where `ReceiptStatusError` comes in.

## What is ReceiptStatusError?

`ReceiptStatusError` is an exception that represents a failure during the **consensus/execution** phase.

*   **Timing:** It happens after the transaction is submitted and processed by the network.
*   **Content:** It contains the `transaction_receipt`, which holds the status code (e.g., `INSUFFICIENT_ACCOUNT_BALANCE`) and other metadata.
*   **Usage:** You must explicitly check the receipt status or configure your client/transaction to throw this error.

## Handling ReceiptStatusError

When you execute a transaction, you typically get a receipt. You should check the status of this receipt.

```python
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.exceptions import ReceiptStatusError

# ... client and transaction setup ...

try:
    # Execute the transaction
    receipt = tx.execute(client)

    # Check if the status is SUCCESS
    if receipt.status != ResponseCode.SUCCESS:
        # Raise the specific error with details
        raise ReceiptStatusError(receipt.status, tx.transaction_id, receipt)

    print("Transaction succeeded!")

except ReceiptStatusError as e:
    print(f"Transaction failed post-consensus: {e}")
    print(f"Status Code: {e.status}")
    print(f"Transaction ID: {e.transaction_id}")
    # You can access the full receipt for debugging
    # print(e.transaction_receipt)

except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

## Summary

*   **Precheck errors** happen *before* the network processes the transaction.
*   **ReceiptStatusErrors** happen *after* the network processes the transaction but finds it invalid according to ledger rules.
*   Always check `receipt.status` to ensure your transaction actually did what you intended.
