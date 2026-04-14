from __future__ import annotations

from enum import Enum

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey


class KeyType(Enum):
    ED25519_PRIVATE_KEY = "ed25519PrivateKey"
    ED25519_PUBLIC_KEY = "ed25519PublicKey"
    ECDSA_SECP256K1_PRIVATE_KEY = "ecdsaSecp256k1PrivateKey"
    ECDSA_SECP256K1_PUBLIC_KEY = "ecdsaSecp256k1PublicKey"
    LIST_KEY = "keyList"
    THRESHOLD_KEY = "thresholdKey"
    EVM_ADDRESS_KEY = "evmAddress"

    @classmethod
    def from_string(cls, key_type_str: str):
        """Helper to get KeyType from string."""
        for key_type in cls:
            if key_type.value == key_type_str:
                return key_type

        raise ValueError(f"Unknown key type: {key_type_str}")


def get_key_from_string(key_string: str) -> Key:
    """Helper to convert the str value to Key."""
    key_bytes = bytes.fromhex(key_string)

    try:
        return Key.from_bytes(key_bytes)
    except Exception:
        pass

    try:
        return PublicKey.from_string_der(key_string)
    except Exception:
        pass

    try:
        return PrivateKey.from_string_der(key_string)
    except Exception:
        pass

    raise ValueError("Invalid key string")
