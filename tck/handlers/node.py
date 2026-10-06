from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction
from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.registry import rpc_method
from tck.param.node import CreateNodeParams, DeleteNodeParams
from tck.response.node import NodeResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import to_int
from tck.util.transaction_utils import execute_validated


def _build_node_create_transaaction(params: CreateNodeParams) -> NodeCreateTransaction:
    """Build NodeCreateTransaction from CreateNodeParasm."""
    transaction = NodeCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))
    if params.description is not None:
        transaction.set_description(params.description)
    if params.gossipEndpoints is not None:
        transaction.set_gossip_endpoints([e.to_sdk_endpoint() for e in params.gossipEndpoints])
    if params.serviceEndpoints is not None:
        transaction.set_service_endpoints([e.to_sdk_endpoint() for e in params.serviceEndpoints])
    if params.gossipCaCertificate is not None:
        transaction.set_gossip_ca_certificate(bytes.fromhex(params.gossipCaCertificate))
    if params.grpcCertificateHash is not None:
        transaction.set_grpc_certificate_hash(bytes.fromhex(params.grpcCertificateHash))
    if params.grpcWebProxyEndpoint is not None:
        transaction.set_grpc_web_proxy_endpoint(params.grpcWebProxyEndpoint.to_sdk_endpoint())
    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))
    if params.declineReward is not None:
        transaction.set_decline_reward(params.declineReward)

    return transaction


@rpc_method("createNode")
def create_node(params: CreateNodeParams) -> NodeResponse:
    """Create a node."""
    client = get_client(params.sessionId)

    transaction = _build_node_create_transaaction(params)
    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)
    node_id = ""

    if receipt.node_id is not None and receipt.node_id > 0:
        node_id = str(receipt.node_id)

    return NodeResponse(node_id, ResponseCode(receipt.status).name)


@rpc_method("deleteNode")
def delete_node(params: DeleteNodeParams) -> NodeResponse:
    """Delete a node."""
    client = get_client(params.sessionId)

    transaction = NodeDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.nodeId is not None:
        transaction.set_node_id(to_int(params.nodeId))

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)
    node_id = ""

    if receipt.node_id is not None and receipt.node_id > 0:
        node_id = str(receipt.node_id)

    return NodeResponse(node_id, ResponseCode(receipt.status).name)
