from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key, KeyList
from tck.errors import JsonRpcError
from tck.handlers.registry import register_handler
from tck.param.key import KeyGenerationParams
from tck.response.key import KeyGenerationResponse
from tck.util.key_utils import KeyType, get_key_from_string

@register_handler("generateKey")
def generate_key(params: KeyGenerationParams) -> KeyGenerationResponse:
  if params.fromKey and params.type not in {
    KeyType.ED25519_PUBLIC_KEY,
    KeyType.ECDSA_SECP256K1_PUBLIC_KEY,
    KeyType.EVM_ADDRESS_KEY,
  }:
    raise JsonRpcError.invalid_params_error(
      "invalid parameters: fromKey is only allowed for "
      "ed25519PublicKey, ecdsaSecp256k1PublicKey, or evmAddress types."
    )

  if params.threshold is not None and params.type is not KeyType.THRESHOLD_KEY:
    raise JsonRpcError.invalid_params_error(
      "invalid parameters: threshold is only allowed for thresholdKey types."
    )

  if params.keys and params.type not in {KeyType.THRESHOLD_KEY, KeyType.LIST_KEY}:
    raise JsonRpcError.invalid_params_error(
      "invalid parameters: keys are only allowed for keyList or thresholdKey types."
    )

  if params.type in {KeyType.THRESHOLD_KEY, KeyType.LIST_KEY} and not params.keys:
    raise JsonRpcError.invalid_params_error(
      "invalid parameters: keys must be provided for keyList or thresholdKey types."
    )
  
  response = KeyGenerationResponse()
  response.key = _process_key_recursively(params=params, response=response, is_list=False)

  return response
  

def _process_key_recursively(params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool) -> str:
  if params.type in {KeyType.ED25519_PRIVATE_KEY, KeyType.ECDSA_SECP256K1_PRIVATE_KEY}:
    if params.type == KeyType.ED25519_PRIVATE_KEY:
      private_key = PrivateKey.generate_ed25519()
    else:
      private_key = PrivateKey.generate_ecdsa()
      
    private_key_string = private_key.to_string_der()
    
    if is_list:
      response.privateKeys.append(private_key_string)

    return private_key_string

  elif params.type in {KeyType.ED25519_PUBLIC_KEY, KeyType.ECDSA_SECP256K1_PUBLIC_KEY}:
    if params.fromKey:
      return (
        PrivateKey.from_string(params.fromKey)
          .public_key()
          .to_string_der()
      )

    if params.type == KeyType.ED25519_PUBLIC_KEY:
      private_key = PrivateKey.generate_ed25519()
    else:
      private_key = PrivateKey.generate_ecdsa()

    if is_list:
      response.privateKeys.append(private_key.to_string_der())

    return private_key.public_key().to_string_der()
  
  elif params.type in {KeyType.LIST_KEY, KeyType.THRESHOLD_KEY}:
    print("IN the prorto")
    keys = []

    for key_params in params.keys:
        key_string = _process_key_recursively(
            params=key_params,
            response=response,
            is_list=True
        )
        keys.append(get_key_from_string(key_string))

    proto_keys = KeyList()

    print(proto_keys)

    for k in keys:
        proto_keys.keys.add().CopyFrom(k)

    pkey = Key()

    if params.type == KeyType.THRESHOLD_KEY:
        pkey.thresholdKey.threshold = params.threshold
        pkey.thresholdKey.keys.CopyFrom(proto_keys)
    else:
        pkey.keyList.CopyFrom(proto_keys)

    return pkey.SerializeToString().hex()

  elif params.type == KeyType.EVM_ADDRESS_KEY:
    if params.fromKey:
      key = get_key_from_string(params.fromKey)

      if isinstance(key, PrivateKey):
        return str(key.public_key().to_evm_address())

      elif isinstance(key, PublicKey):
        return str(key.to_evm_address())

      else:
        raise JsonRpcError.invalid_params_error(
          "invalid parameters: fromKey for evmAddress is not ECDSAsecp256k1."
        )

    return str(
        PrivateKey.generate_ecdsa()
          .public_key()
          .to_evm_address()
      )

  else:
    print(params.type)
    raise JsonRpcError.invalid_params_error("invalid request: key type not recognized.")
