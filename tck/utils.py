from hiero_sdk_python import Network
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from jsonrpcserver import Success, method, InvalidParams
from hiero_sdk_python.crypto.private_key import PrivateKey

__operatorAccountId: AccountId
__operatorPrivateKey: PrivateKey
__client: Client = Client(Network(network='testnet'))

@method
def setup(operatorAccountId: str=None, operatorPrivateKey: str=None, nodeIp: str=None, nodeAccountId: str=None, mirrorNetworkIp: str=None):
    global __client, __operatorAccountId, __operatorPrivateKey
    __operatorAccountId = AccountId.from_string(operatorAccountId)
    __operatorPrivateKey = PrivateKey.from_string(operatorPrivateKey)
    __client.set_operator(__operatorAccountId, __operatorPrivateKey)

    return Success({
        "message":"Successfully setup custom client.",
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
def generateKey(type: str=None, fromKey: str=None, threshold: int=None, keys: list=None):
    if type == "ed25519PublicKey":
        if fromKey is None:
            return Success({"key": PrivateKey.generate_ed25519().public_key().to_string_raw()})
        else:
            new_account_private_key = PrivateKey.from_string(fromKey)
            new_account_public_key = new_account_private_key.public_key()
            return Success({"key": new_account_public_key.to_string_raw()})

    elif type == "ecdsaSecp256k1PublicKey":
        if fromKey is None:
            return Success({"key": PrivateKey.generate_ecdsa().public_key().to_string_raw()})
        else:
            new_account_private_key = PrivateKey.from_string(fromKey)
            new_account_public_key = new_account_private_key.public_key()
            return Success({"key": new_account_public_key.to_string_raw()})

    elif type == "ed25519PrivateKey":
        new_account_private_key = PrivateKey.generate()
        return Success({"key": new_account_private_key.to_string_raw()})

    else:
        return InvalidParams("Unknown type")

