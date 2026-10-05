"""TCK handlers for node service methods."""

from __future__ import annotations

from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode

from tck.handlers.registry import rpc_method
from tck.param.node import DeleteNodeParams
from tck.response.node import DeleteNodeResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.transaction_utils import execute_validated


def _build_delete_node_transaction(params: DeleteNodeParams) -> NodeDeleteTransaction:
    """Build a NodeDeleteTransaction from TCK parameters."""
    transaction = NodeDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.nodeId is not None:
        transaction.set_node_id(int(params.nodeId))

    return transaction


@rpc_method("deleteNode")
def delete_node(params: DeleteNodeParams) -> DeleteNodeResponse:
    """Handle the deleteNode JSON-RPC request."""
    client = get_client(params.sessionId)

    transaction = _build_delete_node_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)

    return DeleteNodeResponse(status=ResponseCode(receipt.status).name)
