from __future__ import annotations

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.node import _Node
from tck.handlers.registry import rpc_method
from tck.param.base import BaseParams
from tck.param.sdk import SetupParams
from tck.response.sdk import SetupResponse
from tck.util.client_utils import get_client, remove_client, store_client


@rpc_method("setup")
def setup_handler(params: SetupParams) -> SetupResponse:
    operator_account_id = AccountId.from_string(params.operatorAccountId)
    operator_private_key = PrivateKey.from_string(params.operatorPrivateKey)

    if params.nodeIp and params.nodeAccountId and params.mirrorNetworkIp:
        client = Client()
        client.network = Network(
            nodes=[_Node(AccountId.from_string(params.nodeAccountId), params.nodeIp, None)],
            mirror_address=params.mirrorNetworkIp,
        )
        client.set_operator(operator_account_id, operator_private_key)

        client_type = "custom"
        store_client(params.sessionId, client)
    else:
        client = Client.for_testnet()
        client_type = "testnet"
        store_client(params.sessionId, client)

    client = get_client(params.sessionId)
    client.set_operator(operator_account_id, operator_private_key)

    return SetupResponse(f"Successfully setup {client_type} client")


@rpc_method("setOperator")
def set_operator(params: SetupParams) -> SetupResponse:
    operator_account_id = AccountId.from_string(params.operatorAccountId)
    operator_private_key = PrivateKey.from_string(params.operatorPrivateKey)

    client = get_client(params.sessionId)
    client.set_operator(operator_account_id, operator_private_key)

    return SetupResponse("")


@rpc_method("reset")
def reset_handler(params: BaseParams) -> SetupResponse:
    client = remove_client(params.sessionId)

    if client is not None:
        client.close()

    return SetupResponse("Successfully reset client")
