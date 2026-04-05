from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.key import KeyGenerationParams
from tck.response.key import KeyGenerationResponse
from tck.util.key_utils import KeyType, get_key_from_string


@rpc_method("generateKey")
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

    if params.threshold is not None and params.type != KeyType.THRESHOLD_KEY:
        raise JsonRpcError.invalid_params_error(
            "invalid parameters: threshold is only allowed for thresholdKey types."
        )

    if params.type == KeyType.THRESHOLD_KEY and params.threshold is None:
        raise JsonRpcError.invalid_params_error(
            "invalid request: threshold is required for generating a ThresholdKey type."
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
    response.key = _process_key_recursively(
        params=params, response=response, is_list=False
    )

    return response


def _handle_private_key(
    params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool
) -> str:
    if params.type == KeyType.ED25519_PRIVATE_KEY:
        private_key = PrivateKey.generate_ed25519()
    else:
        private_key = PrivateKey.generate_ecdsa()

    private_key_string = private_key.to_string_der()

    if is_list:
        response.privateKeys.append(private_key_string)

    return private_key_string


def _handle_public_key(
    params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool
) -> str:
    if params.fromKey:
        return PrivateKey.from_string(params.fromKey).public_key().to_string_der()

    if params.type == KeyType.ED25519_PUBLIC_KEY:
        private_key = PrivateKey.generate_ed25519()
    else:
        private_key = PrivateKey.generate_ecdsa()

    if is_list:
        response.privateKeys.append(private_key.to_string_der())

    return private_key.public_key().to_string_der()


def _handle_key_list(
    params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool
) -> str:
    key_list = KeyList()

    for key_params in params.keys:
        key_string = _process_key_recursively(
            params=key_params, response=response, is_list=True
        )
        key_list.add_key(get_key_from_string(key_string))

    if params.type == KeyType.THRESHOLD_KEY:
        key_list.set_threshold(int(params.threshold))

    return key_list.to_bytes().hex()


def _handle_evm_address(
    params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool
) -> str:
    if params.fromKey:
        key = get_key_from_string(params.fromKey)

        if isinstance(key, PrivateKey):
            return str(key.public_key().to_evm_address())

        if isinstance(key, PublicKey):
            return str(key.to_evm_address())

        raise JsonRpcError.invalid_params_error(
            "invalid parameters: fromKey for evmAddress is not ECDSAsecp256k1."
        )

    return str(PrivateKey.generate_ecdsa().public_key().to_evm_address())


def _process_key_recursively(
    params: KeyGenerationParams, response: KeyGenerationResponse, is_list: bool
) -> str:
    if params.type in {
        KeyType.ED25519_PRIVATE_KEY,
        KeyType.ECDSA_SECP256K1_PRIVATE_KEY,
    }:
        return _handle_private_key(params, response, is_list)
    if params.type in {
        KeyType.ED25519_PUBLIC_KEY,
        KeyType.ECDSA_SECP256K1_PUBLIC_KEY,
    }:
        return _handle_public_key(params, response, is_list)
    if params.type in {KeyType.LIST_KEY, KeyType.THRESHOLD_KEY}:
        return _handle_key_list(params, response, is_list)
    if params.type == KeyType.EVM_ADDRESS_KEY:
        return _handle_evm_address(params, response, is_list)
    raise JsonRpcError.invalid_params_error(
        "invalid request: key type not recognized."
    )
