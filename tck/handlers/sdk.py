from hiero_sdk_python.node import _Node
from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from tck.handlers.registry import register_handler
from tck.param.base import BaseParams
from tck.param.sdk import SetupParams
from tck.response.sdk import SetupResponse

CLIENTS: dict[str, Client] = {}

@register_handler("setup")
def setup_handler(params: SetupParams) -> SetupResponse:
    """Setup handler to initialize SDK clients with operator credentials and network configuration."""
    operator_account_id = AccountId.from_string(params.operatorAccountId)
    operator_private_key = PrivateKey.from_string(params.operatorPrivateKey)

    if (params.nodeIp and params.nodeAccountId and params.mirrorNetworkIp):
        client = Client()
        client.network = Network(
            nodes=[_Node(AccountId.from_string(params.nodeAccountId), params.nodeIp, None)], 
            mirror_address=params.mirrorNetworkIp
        )
        client.set_operator(operator_account_id, operator_private_key)

        client_type = "custom"
        CLIENTS[params.sessionId] = client
    else:
        client = Client.for_testnet()
        client_type = "testnet"
        CLIENTS[params.sessionId] = client

    client = CLIENTS.get(params.sessionId)
    client.set_operator(operator_account_id, operator_private_key)

    return SetupResponse(f"Successfully setup {client_type} client")


@register_handler("setOperator")
def set_operator(params: SetupParams) -> SetupResponse:
    operator_account_id = AccountId.from_string(params.operatorAccountId)
    operator_private_key = PrivateKey.from_string(params.operatorPrivateKey)

    client = CLIENTS.get(params.sessionId)
    client.set_operator(operator_account_id, operator_private_key)

    return SetupResponse("")


@register_handler("reset")
def reset_handler(params: BaseParams) -> SetupResponse:
    """Reset handler to close connections and clear client state."""
    print(params)
    client = CLIENTS.pop(params.sessionId)
    
    if client is not None:
        client.close()
    
    return SetupResponse("Successfully reset client")

