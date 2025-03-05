import logging

from hiero_sdk_python import Network
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from jsonrpcserver import Success, method, JsonRpcError
from hiero_sdk_python.crypto.private_key import PrivateKey

# testnet variables
__operatorAccountId: AccountId
__operatorPrivateKey: PrivateKey
__client = Client(network="testnet")

# custom network variables
__usingPrivateNetwork: bool = False
__nodeIp: str
__nodeAccountId: AccountId
__mirrorNetworkIp: str

@method
def setup(operatorAccountId: str=None, operatorPrivateKey: str=None, nodeIp: str=None, nodeAccountId: str=None, mirrorNetworkIp: str=None):
    global __client, __operatorAccountId, __operatorPrivateKey, __nodeIp, __nodeAccountId, __mirrorNetworkIp, __usingPrivateNetwork
    __operatorAccountId = AccountId.from_string(operatorAccountId)
    __operatorPrivateKey = PrivateKey.from_string(operatorPrivateKey)

    __nodeIp = nodeIp
    __nodeAccountId = nodeAccountId
    __mirrorNetworkIp = mirrorNetworkIp

    if __nodeIp is not None:
        __usingPrivateNetwork = True
        __client = Client(network=Network(network="custom", nodes=[(__nodeIp,__nodeAccountId)], mirror_address=__mirrorNetworkIp))

    __client.set_operator(__operatorAccountId, __operatorPrivateKey)

    return Success({
        "message":"Successfully setup testnet client.",
        "status":"SUCCESS"
    })

@method
def reset():
    global  __operatorAccountId, __operatorPrivateKey, __client
    __operatorAccountId = None
    __operatorPrivateKey = None
    __client = Client(Network(network='testnet'))

    return Success({
        "message":"Successfully reset client.",
        "status":"SUCCESS"
    })

@method
def generateKey(type: str, fromKey: str=None, threshold: int=None, keys: list=None):
    pk = None

    if type == "ed25519PrivateKey":
        return Success({
            "key": PrivateKey.generate_ed25519().to_string_raw(),
        })

    elif type == "ed25519PublicKey":
        if fromKey is None:
            pk = PrivateKey.generate()
        else:
            pk = PrivateKey.from_string(fromKey)
        return Success({
            "key": pk.public_key().to_string_raw(),
        })

    elif type == "ecdsaSecp256k1PrivateKey":
        return Success({
            "key": PrivateKey.generate_ecdsa().to_string_raw(),
        })

    elif type == "ecdsaSecp256k1PublicKey":
        if fromKey is None:
            pk = PrivateKey.generate_ecdsa()
        else:
            pk = PrivateKey.from_string(fromKey)
        return Success({
            "key": pk.public_key().to_string_raw(),
        })

    elif type == "thresholdKey":
        return JsonRpcError(code=-32001, message="Not implemented")

    elif type == "keyList":
        return JsonRpcError(code=-32001, message="Not implemented")

    elif type == "evmAddress":
        return JsonRpcError(code=-32001, message="Not implemented")

    else:
        return JsonRpcError(code=-32001, message="Unknown key type")