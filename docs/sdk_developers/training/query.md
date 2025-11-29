# Understanding Queries in Hiero SDK

## Introduction

In the Hiero SDK, **Query** is a fundamental concept. It represents a request to the Hedera network to retrieve data without changing the network state. Unlike transactions, queries typically do not alter the ledger, although they may require a small payment to cover the cost of processing.

This guide explains how the `Query` class works, its relationship with `_Executable`, and how to implement your own custom queries.

## Contents

- [What is a Query?](#what-is-a-query)
- [Architecture](#architecture)
  - [Inheritance Hierarchy](#inheritance-hierarchy)
  - [Key Concepts](#key-concepts)
- [Execution Flow](#execution-flow)
- [Query Payment](#query-payment)
  - [Automatic Cost Determination](#automatic-cost-determination)
- [Retry Logic](#retry-logic)
- [Building a Custom Query](#building-a-custom-query)
  - [Abstract Methods](#abstract-methods)
  - [Example Implementation](#example-implementation)
- [Summary](#summary)

---

## What is a Query?

The `Query` class is the base class for all Hedera network queries. Queries allow you to request data from the Hedera network, such as:

- Account balances
- Transaction records
- Token information
- Topic messages
- File contents

Unlike transactions, queries do not change the network state. However, because processing a query consumes resources on the node, some queries require a payment in HBAR.

## Architecture

### Inheritance Hierarchy

All queries in the SDK inherit from the `Query` class, which in turn inherits from `_Executable`.

```
_Executable
   └── Query
        ├── AccountBalanceQuery
        ├── TransactionRecordQuery
        ├── TokenInfoQuery
        └── ... (other specific queries)
```

This inheritance structure means that `Query` benefits from the unified execution engine provided by `_Executable`, including:

- **Automatic retries**: Handles temporary network failures.
- **Node selection and rotation**: Automatically selects healthy nodes.
- **gRPC network call orchestration**: Manages the underlying communication.
- **Logging and error handling**: Provides consistent diagnostics.

### Key Concepts

`Query` acts as a bridge between the high-level user request and the low-level gRPC calls. It handles:

1.  **Payment Management**: Ensuring the node is paid for the query.
2.  **Request Construction**: Building the Protobuf messages.
3.  **Response Parsing**: Converting Protobuf responses into SDK objects.

---

## Execution Flow

When you call `.execute(client)` on a query object, the following steps occur:

1.  **Pre-execution setup (`_before_execute`)**:
    -   Assigns nodes and an operator from the client.
    -   Determines if payment is required.
    -   If no payment is set, it may query the network for the cost.

2.  **Request building (`_make_request`)**:
    -   Constructs the Protobuf request for the specific query type.
    -   Includes the payment transaction (if required) in the request header.

3.  **gRPC call (`_get_method` + `_execute_method`)**:
    -   Sends the request to the selected node using the appropriate gRPC method.
    -   Handles retries and backoff strategies for temporary failures.

4.  **Response mapping (`_map_response`)**:
    -   Receives the raw Protobuf response.
    -   Converts it into a usable SDK object (or extracts the relevant part).

5.  **Retry handling (`_should_retry`)**:
    -   Checks the response status code.
    -   Automatically retries queries with statuses like `BUSY` or `PLATFORM_NOT_ACTIVE`.

6.  **Error mapping (`_map_status_error`)**:
    -   If the query fails (e.g., `INVALID_ACCOUNT_ID`), converts the status into a Python exception like `PrecheckError` or `ReceiptStatusError`.

---

## Query Payment

Some queries require a payment to the node. This payment is handled via a small `CryptoTransfer` transaction attached to the query request header.

### Setting Custom Payment

You can manually set the payment amount if you know the cost or want to offer a specific fee:

```python
from hiero_sdk_python.hbar import Hbar

query = AccountBalanceQuery(account_id)
query.set_query_payment(Hbar(1)) # Set custom payment to 1 Hbar
```

### Automatic Cost Determination

If no payment is set, the SDK can automatically query the cost before executing the actual query.

1.  The SDK sends a lightweight "Cost Query" (`COST_ANSWER` mode).
2.  The network returns the required fee.
3.  The SDK sets this fee as the payment and executes the actual query (`ANSWER_ONLY` mode).

You can also manually fetch the cost:

```python
cost = query.get_cost(client)
print(f"Query cost: {cost} Hbar")
```

The SDK constructs a signed payment transaction using the operator’s private key to pay for the query.

---

## Retry Logic

Queries automatically handle retries for certain network issues. The base `_should_retry` implementation handles these statuses:

-   `BUSY`: The node is busy.
-   `PLATFORM_TRANSACTION_NOT_CREATED`: The transaction wasn't created on the platform.
-   `PLATFORM_NOT_ACTIVE`: The platform is not active.

Subclasses can override `_should_retry` to add custom retry logic if needed.

---

## Building a Custom Query

If you need to implement a new type of query (e.g., for a new Hedera service), you can subclass `Query`.

### Abstract Methods

Subclasses **must** implement the following methods:

| Method | Purpose |
| :--- | :--- |
| `_make_request()` | Builds the Protobuf request for the specific query. |
| `_get_query_response(response)` | Extracts the specific query response field from the full network response. |
| `_get_method(channel)` | Returns the gRPC method wrapper (`_Method`) to call for this query. |

Optionally, you can override:

| Method | Purpose |
| :--- | :--- |
| `_map_response(response, node_id, proto_request)` | Customize how the response is returned to the user. |
| `_should_retry(response)` | Customize retry logic. |
| `_map_status_error(response)` | Customize error mapping. |

### Example Implementation

Here is an example of how to implement a simple `AccountBalanceQuery`:

```python
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import query_pb2, crypto_get_account_balance_pb2

class CustomAccountBalanceQuery(Query):
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id

    def _make_request(self):
        # Create the header (includes payment)
        header = self._make_request_header()
        
        # Create the specific query body
        body = crypto_get_account_balance_pb2.CryptoGetAccountBalanceQuery(
            header=header,
            accountID=self.account_id._to_proto()
        )
        
        # Wrap it in the main Query object
        return query_pb2.Query(cryptoGetAccountBalance=body)

    def _get_query_response(self, response):
        # Extract the balance response from the main response
        return response.cryptoGetAccountBalance

    def _get_method(self, channel):
        # Return the gRPC method to call
        return _Method(query_func=channel.crypto.get_account_balance)

# Usage
# query = CustomAccountBalanceQuery(my_account_id)
# balance = query.execute(client)
```

---

## Summary

-   **Query** handles all network-level logic; subclasses only implement query-specific behavior.
-   **Payment** is handled transparently, with support for automatic cost fetching.
-   **Reliability** is ensured through automatic retry and error handling.
-   **Extensibility** is achieved by subclassing `Query` and implementing the required abstract methods.
