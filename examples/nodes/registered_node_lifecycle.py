"""
Demonstrates a HIP-1137 registered-node lifecycle.

This example shows:
1. Create a registered node with one or more service endpoints.
2. Read the registered_node_id from the transaction receipt.
3. Update the registered node metadata.
4. Associate the registered node with an existing consensus node.
5. Delete the registered node.

Notes:
- This flow needs network support for HIP-1137 features.
- GeneralServiceEndpoint is deferred until protobuf support is available.
- RegisteredNodeAddressBookQuery remains unavailable until mirror-node APIs are defined.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

import grpc
from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    BlockNodeApi,
    BlockNodeServiceEndpoint,
    Client,
    NodeUpdateTransaction,
    PrivateKey,
    RegisteredNodeCreateTransaction,
    RegisteredNodeDeleteTransaction,
    RegisteredNodeUpdateTransaction,
    ResponseCode,
)
from hiero_sdk_python.address_book.general_service_endpoint import (
    GeneralServiceEndpoint,
)


T = TypeVar("T")


def _must_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing environment variable: {key}")
    return value


def _optional_int_env(key: str) -> int | None:
    value = os.getenv(key)
    if not value:
        return None
    return int(value)


def _is_unimplemented_rpc_error(exc: grpc.RpcError) -> bool:
    return exc.code() == grpc.StatusCode.UNIMPLEMENTED


def _execute_or_skip(operation: Callable[[], T], skip_message: str) -> T | None:
    try:
        return operation()
    except grpc.RpcError as exc:
        if _is_unimplemented_rpc_error(exc):
            print(skip_message)
            return None
        raise


def _require_success(receipt: Any, action: str) -> None:
    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"{action} failed with status: {ResponseCode(receipt.status).name}")


def _build_update_transaction(
    registered_node_id: int,
    block_endpoint: BlockNodeServiceEndpoint,
) -> RegisteredNodeUpdateTransaction:
    update_tx = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(registered_node_id)
        .set_description("Updated block node")
        .add_service_endpoint(block_endpoint)
    )

    try:
        return update_tx.add_service_endpoint(
            GeneralServiceEndpoint(
                domain_name="general.example.com",
                port=443,
                requires_tls=True,
                description="General endpoint",
            )
        )
    except NotImplementedError:
        # Current protobuf/network does not support this subtype yet.
        print("Skipping GeneralServiceEndpoint: unavailable in current protobuf schema.")
        return update_tx


def _associate_registered_node(client: Client, node_id: int | None, registered_node_id: int) -> None:
    if node_id is None:
        print("Skipping consensus-node association: CONSENSUS_NODE_ID is not set.")
        return

    associate_receipt = _execute_or_skip(
        lambda: (
            NodeUpdateTransaction()
            .set_node_id(node_id)
            .add_associated_registered_node(registered_node_id)
            .execute(client)
        ),
        "Skipping consensus-node association: node update RPC is unavailable on this network.",
    )
    if associate_receipt is None:
        return

    _require_success(associate_receipt, "Node association")


def registered_node_lifecycle() -> None:
    load_dotenv()

    operator_id = AccountId.from_string(_must_env("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(_must_env("OPERATOR_KEY"))
    node_id_to_update = _optional_int_env("CONSENSUS_NODE_ID")

    client = Client.for_testnet()
    client.set_operator(operator_id, operator_key)

    registered_node_admin_key = PrivateKey.generate_ed25519()

    block_endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.SUBSCRIBE_STREAM,
    )

    create_tx = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(registered_node_admin_key.public_key())
        .set_description("Example block node")
        .add_service_endpoint(block_endpoint)
        .freeze_with(client)
        .sign(registered_node_admin_key)
    )

    create_receipt = _execute_or_skip(
        lambda: create_tx.execute(client),
        "Skipping example: network does not support HIP-1137 registered-node RPC methods yet.",
    )
    if create_receipt is None:
        return
    _require_success(create_receipt, "Create")

    registered_node_id = create_receipt.registered_node_id
    if registered_node_id is None:
        raise RuntimeError("Create succeeded but no registered_node_id was returned.")

    update_tx = _build_update_transaction(registered_node_id, block_endpoint)

    update_receipt = _execute_or_skip(
        lambda: update_tx.freeze_with(client).sign(registered_node_admin_key).execute(client),
        "Skipping remaining lifecycle steps: registered-node update RPC is unavailable on this network.",
    )
    if update_receipt is None:
        return
    _require_success(update_receipt, "Update")

    _associate_registered_node(client, node_id_to_update, registered_node_id)

    delete_receipt = _execute_or_skip(
        lambda: (
            RegisteredNodeDeleteTransaction()
            .set_registered_node_id(registered_node_id)
            .freeze_with(client)
            .sign(registered_node_admin_key)
            .execute(client)
        ),
        "Skipping delete step: registered-node delete RPC is unavailable on this network.",
    )
    if delete_receipt is None:
        return
    _require_success(delete_receipt, "Delete")

    print(f"Lifecycle complete for registered node id: {registered_node_id}")


if __name__ == "__main__":
    registered_node_lifecycle()
