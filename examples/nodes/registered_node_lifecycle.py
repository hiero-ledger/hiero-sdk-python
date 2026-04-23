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


def _is_unimplemented_rpc_error(exc: BaseException) -> bool:
    return isinstance(exc, grpc.RpcError) and exc.code() == grpc.StatusCode.UNIMPLEMENTED


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

    try:
        create_receipt = create_tx.execute(client)
    except Exception as exc:  # noqa: BLE001
        if _is_unimplemented_rpc_error(exc):
            print("Skipping example: network does not support HIP-1137 registered-node RPC methods yet.")
            return
        raise
    if create_receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Create failed with status: {ResponseCode(create_receipt.status).name}")

    registered_node_id = create_receipt.registered_node_id
    if registered_node_id is None:
        raise RuntimeError("Create succeeded but no registered_node_id was returned.")

    update_tx = (
        RegisteredNodeUpdateTransaction()
        .set_registered_node_id(registered_node_id)
        .set_description("Updated block node")
        .add_service_endpoint(block_endpoint)
    )

    try:
        update_tx = update_tx.add_service_endpoint(
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

    try:
        update_receipt = update_tx.freeze_with(client).sign(registered_node_admin_key).execute(client)
    except Exception as exc:  # noqa: BLE001
        if _is_unimplemented_rpc_error(exc):
            print("Skipping remaining lifecycle steps: registered-node update RPC is unavailable on this network.")
            return
        raise
    if update_receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Update failed with status: {ResponseCode(update_receipt.status).name}")

    if node_id_to_update is None:
        print("Skipping consensus-node association: CONSENSUS_NODE_ID is not set.")
    else:
        try:
            associate_receipt = (
                NodeUpdateTransaction()
                .set_node_id(node_id_to_update)
                .add_associated_registered_node(registered_node_id)
                .execute(client)
            )
        except Exception as exc:  # noqa: BLE001
            if _is_unimplemented_rpc_error(exc):
                print("Skipping consensus-node association: node update RPC is unavailable on this network.")
                associate_receipt = None
            else:
                raise
        if associate_receipt is None:
            pass
        elif associate_receipt.status != ResponseCode.SUCCESS:
            raise RuntimeError(f"Node association failed with status: {ResponseCode(associate_receipt.status).name}")

    try:
        delete_receipt = (
            RegisteredNodeDeleteTransaction()
            .set_registered_node_id(registered_node_id)
            .freeze_with(client)
            .sign(registered_node_admin_key)
            .execute(client)
        )
    except Exception as exc:  # noqa: BLE001
        if _is_unimplemented_rpc_error(exc):
            print("Skipping delete step: registered-node delete RPC is unavailable on this network.")
            return
        raise
    if delete_receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Delete failed with status: {ResponseCode(delete_receipt.status).name}")

    print(f"Lifecycle complete for registered node id: {registered_node_id}")


if __name__ == "__main__":
    registered_node_lifecycle()
