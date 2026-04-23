# HIP-1137 Coverage in hiero-sdk-python

This document maps HIP-1137 concepts to current SDK implementation status.

## Covered Concepts

- `BlockNodeApi` enum: [src/hiero_sdk_python/address_book/block_node_api.py](../../src/hiero_sdk_python/address_book/block_node_api.py)
- `RegisteredServiceEndpoint` base type with IP/FQDN one-of validation:
  [src/hiero_sdk_python/address_book/registered_service_endpoint.py](../../src/hiero_sdk_python/address_book/registered_service_endpoint.py)
- Endpoint subtypes:
  - Block: [src/hiero_sdk_python/address_book/block_node_service_endpoint.py](../../src/hiero_sdk_python/address_book/block_node_service_endpoint.py)
  - Mirror: [src/hiero_sdk_python/address_book/mirror_node_service_endpoint.py](../../src/hiero_sdk_python/address_book/mirror_node_service_endpoint.py)
  - RPC relay: [src/hiero_sdk_python/address_book/rpc_relay_service_endpoint.py](../../src/hiero_sdk_python/address_book/rpc_relay_service_endpoint.py)
  - General service: [src/hiero_sdk_python/address_book/general_service_endpoint.py](../../src/hiero_sdk_python/address_book/general_service_endpoint.py)
- Registered node transactions:
  - Create: [src/hiero_sdk_python/nodes/registered_node_create_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_create_transaction.py)
  - Update: [src/hiero_sdk_python/nodes/registered_node_update_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_update_transaction.py)
  - Delete: [src/hiero_sdk_python/nodes/registered_node_delete_transaction.py](../../src/hiero_sdk_python/nodes/registered_node_delete_transaction.py)
- `TransactionReceipt.registered_node_id`:
  [src/hiero_sdk_python/transaction/transaction_receipt.py](../../src/hiero_sdk_python/transaction/transaction_receipt.py)
- Consensus node association fields:
  - Create: [src/hiero_sdk_python/nodes/node_create_transaction.py](../../src/hiero_sdk_python/nodes/node_create_transaction.py)
  - Update (including clear semantics): [src/hiero_sdk_python/nodes/node_update_transaction.py](../../src/hiero_sdk_python/nodes/node_update_transaction.py)
- HIP-1137 response codes (public SDK enum):
  - [src/hiero_sdk_python/response_code.py](../../src/hiero_sdk_python/response_code.py)
- Registered node read models:
  - [src/hiero_sdk_python/address_book/registered_node.py](../../src/hiero_sdk_python/address_book/registered_node.py)
  - [src/hiero_sdk_python/address_book/registered_node_address_book.py](../../src/hiero_sdk_python/address_book/registered_node_address_book.py)

## Deferred Concept (Intentional)

- `RegisteredNodeAddressBookQuery` execution is intentionally deferred until mirror-node API support is defined, matching HIP guidance:
  [src/hiero_sdk_python/address_book/registered_node_address_book_query.py](../../src/hiero_sdk_python/address_book/registered_node_address_book_query.py)
- End-to-end integration coverage for the registered-node lifecycle remains gated on environment/network support in CI:
  [tests/integration/registered_node_transaction_e2e_test.py](../../tests/integration/registered_node_transaction_e2e_test.py)

## Tests

- Endpoint tests (including general subtype when protobuf supports it):
  [tests/unit/registered_service_endpoint_test.py](../../tests/unit/registered_service_endpoint_test.py)
- Registered-node transaction tests:
  - [tests/unit/registered_node_create_transaction_test.py](../../tests/unit/registered_node_create_transaction_test.py)
  - [tests/unit/registered_node_update_transaction_test.py](../../tests/unit/registered_node_update_transaction_test.py)
  - [tests/unit/registered_node_delete_transaction_test.py](../../tests/unit/registered_node_delete_transaction_test.py)
- Node association tests:
  - [tests/unit/node_create_transaction_test.py](../../tests/unit/node_create_transaction_test.py)
  - [tests/unit/node_update_transaction_test.py](../../tests/unit/node_update_transaction_test.py)
- Receipt field test:
  [tests/unit/test_transaction_receipt.py](../../tests/unit/test_transaction_receipt.py)

## Example

- Registered node lifecycle example:
  [examples/nodes/registered_node_lifecycle.py](../../examples/nodes/registered_node_lifecycle.py)
