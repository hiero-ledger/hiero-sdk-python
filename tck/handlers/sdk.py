from __future__ import annotations

from hiero_sdk_python import AccountId, Client, PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.base import BaseParams
from tck.param.sdk import PingParams, SetupParams
from tck.response.sdk import PingResponse, SetupResponse
from tck.util.client_utils import get_client, remove_client, store_client


@rpc_method("setup")
def setup_handler(params: SetupParams) -> SetupResponse:
    operator_account_id = AccountId.from_string(params.operatorAccountId)
    operator_private_key = PrivateKey.from_string(params.operatorPrivateKey)

    if params.nodeIp and params.nodeAccountId and params.mirrorNetworkIp:
        nodes = {params.nodeIp: AccountId.from_string(params.nodeAccountId)}

        client = Client.for_network(network_map=nodes)
        client.network.mirror_address = params.mirrorNetworkIp

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


@rpc_method("ping")
def ping_handler(params: PingParams) -> PingResponse:
    client = get_client(params.sessionId)
    node_account_id = AccountId.from_string(params.nodeAccountId)

    try:
        client.ping(node_account_id)
    except MaxAttemptsError as e:
        raise JsonRpcError.internal_error() from e
    except ValueError as e:
        raise JsonRpcError.internal_error({"message": str(e)}) from e

    return PingResponse(f"Successfully pinged node {params.nodeAccountId}.")


@rpc_method("pingAll")
def ping_all_handler(params: BaseParams) -> PingResponse:
    client = get_client(params.sessionId)
    try:
        client.ping_all()
    except MaxAttemptsError as e:
        raise JsonRpcError.internal_error() from e
    except ValueError as e:
        raise JsonRpcError.internal_error({"message": str(e)}) from e

    return PingResponse("Successfully pinged all nodes.")
