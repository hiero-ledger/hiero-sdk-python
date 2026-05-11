# Error Handling

The Hiero Python SDK raises structured exceptions at three distinct stages of the transaction lifecycle. Understanding when each exception is thrown and what information it carries helps you write resilient applications.

## Overview

Every transaction you submit passes through three stages, each of which can raise a distinct exception:

1. **Pre-consensus validation (precheck)** — the receiving node validates the transaction before forwarding it to the network. Failures here raise `PrecheckError`.
2. **Network retry** — if the node is busy or unreachable, the SDK retries automatically. When retries are exhausted, `MaxAttemptsError` is raised.
3. **Receipt validation** — after consensus, the SDK fetches a receipt and checks its status. A non-`SUCCESS` status raises `ReceiptStatusError`.

## PrecheckError

**When raised:** A node rejected the transaction before it reached consensus. Common causes are an insufficient fee, an expired transaction, or an invalid signature.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `status` | `ResponseCode` | The precheck status code returned by the node |
| `transaction_id` | `TransactionId or None` | The ID of the rejected transaction |
| `message` | `str` | Human-readable error string |

**Common status codes:**

- `INSUFFICIENT_TX_FEE` — the attached fee is too low
- `INVALID_SIGNATURE` — one or more signatures are missing or incorrect
- `TRANSACTION_EXPIRED` — the transaction valid window has passed
- `PAYER_ACCOUNT_NOT_FOUND` — the payer account does not exist

**Example:**

```python
from hiero_sdk_python.exceptions import PrecheckError

try:
    transaction.execute(client)
except PrecheckError as e:
    print(f"Precheck failed: {e.status.name} ({int(e.status)})")
    print(f"Transaction ID: {e.transaction_id}")
```

## MaxAttemptsError

**When raised:** The SDK exhausted all retry attempts without a successful response. This typically occurs when a node is consistently busy (`BUSY` status) or when a network timeout is hit on every attempt.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `node_id` | `str` | The node that was being contacted on the final attempt |
| `last_error` | `BaseException or None` | The underlying error from the last attempt (may be a gRPC error or another exception) |
| `message` | `str` | Human-readable error string |

**Note:** `last_error` wraps the root cause — it may be a `PrecheckError` (from a node returning `BUSY`) or a low-level gRPC transport error.

**Example:**

```python
from hiero_sdk_python.exceptions import MaxAttemptsError

try:
    transaction.execute(client)
except MaxAttemptsError as e:
    print(f"All attempts exhausted. Last node tried: {e.node_id}")
    if e.last_error:
        print(f"Root cause: {e.last_error}")
```

## ReceiptStatusError

**When raised:** The transaction reached consensus but the network returned a non-`SUCCESS` status in the receipt. This is the most common error for logic failures (e.g. insufficient balance, token not associated).

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `status` | `ResponseCode` | The error status from the receipt |
| `transaction_id` | `TransactionId or None` | The ID of the failed transaction |
| `transaction_receipt` | `TransactionReceipt` | The full receipt object |
| `message` | `str` | Human-readable error string |

**Note:** Receipt validation is controlled by the `validate_status` parameter on `get_receipt()`. When set to `False`, the method returns the receipt without raising even for non-`SUCCESS` statuses.

**Example:**

```python
from hiero_sdk_python.exceptions import ReceiptStatusError

try:
    receipt = transaction.execute(client).get_receipt(client)
except ReceiptStatusError as e:
    print(f"Transaction failed at consensus: {e.status.name} ({int(e.status)})")
    print(f"Transaction ID: {e.transaction_id}")
    print(f"Full receipt: {e.transaction_receipt}")
```

## Understanding ResponseCode

`ResponseCode` is an `IntEnum` with approximately 394 named values representing every status the Hedera network can return.

**Key values:**

| Name | Integer | Meaning |
|---|---|---|
| `OK` | 0 | Request accepted (not yet processed) |
| `BUSY` | 12 | Node is too busy; SDK will retry |
| `UNKNOWN` | 21 | Status could not be determined |
| `SUCCESS` | 22 | Transaction succeeded |

**Accessing values:**

```python
from hiero_sdk_python.response_code import ResponseCode

code = ResponseCode.INSUFFICIENT_TX_FEE
print(code.name)    # "INSUFFICIENT_TX_FEE"
print(int(code))    # integer value

# Synthetic codes (returned when the status is unrecognised) expose is_unknown
if code.is_unknown:
    print("Unrecognised status code")
```

**Note:** `ResponseCode` does not include built-in human-readable descriptions beyond the enum name. Refer to the [Hedera status code reference](https://docs.hedera.com/hedera/sdks-and-apis/hedera-api/miscellaneous/responsecode) for full descriptions.

## Practical Example

```python
from hiero_sdk_python.exceptions import PrecheckError, MaxAttemptsError, ReceiptStatusError
from hiero_sdk_python.response_code import ResponseCode

try:
    receipt = transaction.execute(client).get_receipt(client)
    print("Transaction succeeded!")
except PrecheckError as e:
    # Rejected before consensus — fix the transaction and resubmit
    print(f"Precheck failed: {e.status.name}")
    print(f"Transaction ID: {e.transaction_id}")
except ReceiptStatusError as e:
    # Reached consensus but failed — inspect the receipt for details
    print(f"Consensus failure: {e.status.name}")
    print(f"Transaction ID: {e.transaction_id}")
except MaxAttemptsError as e:
    # Network issue — safe to retry after a backoff
    print(f"Network error on node {e.node_id}: {e.last_error}")
```

## Retry and Backoff Guidance

**Automatically retried by the SDK:**

The SDK retries requests internally when a node returns transient statuses such as `BUSY` or `PLATFORM_NOT_ACTIVE`. You do not need to handle these yourself.

**Do not retry without fixing the root cause:**

- `INSUFFICIENT_TX_FEE` — increase the transaction fee
- `INVALID_SIGNATURE` — verify that all required keys have signed
- `TRANSACTION_EXPIRED` — create and sign a new transaction with a fresh valid window
- `ACCOUNT_DELETED` / `TOKEN_NOT_ASSOCIATED_TO_ACCOUNT` — resolve the account or token state first

**Manual retry is appropriate for `MaxAttemptsError`:**

If `MaxAttemptsError` is raised due to a temporary network disruption, a manual retry with exponential backoff is safe:

```python
import time
from hiero_sdk_python.exceptions import MaxAttemptsError

for attempt in range(3):
    try:
        receipt = transaction.execute(client).get_receipt(client)
        break
    except MaxAttemptsError:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
```

## See Also

- [examples/errors/precheck_error.py](../../examples/errors/precheck_error.py) — runnable `PrecheckError` example
- [examples/errors/receipt_status_error.py](../../examples/errors/receipt_status_error.py) — runnable `ReceiptStatusError` example
- [examples/errors/max_attempts_error.py](../../examples/errors/max_attempts_error.py) — runnable `MaxAttemptsError` example
- [receipt_status_error.md](../sdk_developers/training/receipt_status_error.md) — internal training doc on receipt status errors
