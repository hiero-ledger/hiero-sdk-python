from __future__ import annotations

import ipaddress

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.address_book_query import AddressBookQuery
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction
from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.registry import rpc_method
from tck.param.node import CreateNodeParams, DeleteNodeParams, UpdateNodeParams, GetAddressBookParams
from tck.response.base import StatusOnlyResponse
from tck.response.node import (
    EndpointResponse,
    GetAddressBookResponse,
    NodeAddressResponse,
    NodeResponse,
)
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import decode_hex, to_int
from tck.util.transaction_utils import execute_validated


def _build_node_create_transaction(params: CreateNodeParams) -> NodeCreateTransaction:
    """Build NodeCreateTransaction from CreateNodeParams."""
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
        transaction.set_gossip_ca_certificate(decode_hex(params.gossipCaCertificate))
    if params.grpcCertificateHash is not None:
        transaction.set_grpc_certificate_hash(decode_hex(params.grpcCertificateHash))
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

    transaction = _build_node_create_transaction(params)
    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)
    node_id = None

    if receipt.node_id is not None and receipt.node_id > 0:
        node_id = str(receipt.node_id)

    return NodeResponse(node_id, ResponseCode(receipt.status).name)


def _build_node_update_transaction(params: UpdateNodeParams) -> NodeUpdateTransaction:
    """Build NodeUpdateTransaction from UpdateNodeParams."""
    transaction = NodeUpdateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.nodeId is not None:
        transaction.set_node_id(to_int(params.nodeId))
    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))
    if params.description is not None:
        transaction.set_description(params.description)
    if params.gossipEndpoints is not None:
        transaction.set_gossip_endpoints([e.to_sdk_endpoint() for e in params.gossipEndpoints])
    if params.serviceEndpoints is not None:
        transaction.set_service_endpoints([e.to_sdk_endpoint() for e in params.serviceEndpoints])
    if params.gossipCaCertificate is not None:
        transaction.set_gossip_ca_certificate(decode_hex(params.gossipCaCertificate))
    if params.grpcCertificateHash is not None:
        transaction.set_grpc_certificate_hash(decode_hex(params.grpcCertificateHash))
    if params.grpcWebProxyEndpoint is not None:
        transaction.set_grpc_web_proxy_endpoint(params.grpcWebProxyEndpoint.to_sdk_endpoint())
    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))
    if params.declineReward is not None:
        transaction.set_decline_reward(params.declineReward)

    return transaction


@rpc_method("updateNode")
def update_node(params: UpdateNodeParams) -> StatusOnlyResponse:
    """Update a node."""
    client = get_client(params.sessionId)

    transaction = _build_node_update_transaction(params)
    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)

    return StatusOnlyResponse(ResponseCode(receipt.status).name)


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
    node_id = None

    if receipt.node_id is not None and receipt.node_id > 0:
        node_id = str(receipt.node_id)

    return NodeResponse(node_id, ResponseCode(receipt.status).name)


def _map_to_node_address_response(address: NodeAddress) -> NodeAddressResponse:
    """Helper to map the SDK NodeAddress to JSON-RPC NodeAddressResponse."""
    endpoints = [
        # from_dict and from_proto store the address int b"127.0.0.1" format.
        EndpointResponse(
            ipAddressV4=(
                ipaddress.ip_address(endpoint._address.decode("utf-8")).packed.hex() if endpoint._address else None
            ),
            port=endpoint._port,
            domainName=endpoint._domain_name,
        )
        for endpoint in address._addresses
    ]

    return NodeAddressResponse(
        rsaPublicKey=address._public_key,
        accountId=str(address._account_id) if address._account_id is not None else None,
        nodeId=address._node_id,
        nodeCertHash=bytes.hex(address._cert_hash) if address._cert_hash is not None else None,
        serviceEndpoints=endpoints,
        description=address._description,
        stake=address._stake,
    )


@rpc_method("getAddressBook")
def get_address_book(params: GetAddressBookParams) -> GetAddressBookResponse:
    """Get address book query."""
    client = get_client(params.sessionId)

    query = AddressBookQuery()
    if params.fileId is not None:
        query.set_file_id(FileId.from_string(params.fileId))
    if params.limit is not None:
        query.set_limit(params.limit)

    address_book = query.execute(client)
    return GetAddressBookResponse(
        nodeAddresses=[_map_to_node_address_response(address) for address in address_book.node_addresses]
    )
