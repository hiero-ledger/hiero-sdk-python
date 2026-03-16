"""Utilities for working with cryptographic keys."""

from __future__ import annotations

from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.crypto.threshold_key import ThresholdKey
from hiero_sdk_python.hapi.services import basic_types_pb2

# Type alias for supported SDK key types
Key = PrivateKey | PublicKey | KeyList | ThresholdKey


def key_to_proto(key: Key | None) -> basic_types_pb2.Key | None:
    """
    Helper function to convert an SDK key to protobuf Key format.

    This function handles the conversion of SDK key types to protobuf format:
    - If a PrivateKey is provided, its corresponding public key is extracted and converted.
    - If a PublicKey is provided, it is converted directly to protobuf.
    - If a KeyList or ThresholdKey is provided, it is converted recursively.
    - If None is provided, None is returned.

    Args:
        key (Optional[Key]): The key to convert, or None.

    Returns:
        basic_types_pb2.Key (Optional): The protobuf key or None if key is None.

    Raises:
        TypeError: If the provided key is not a supported SDK key type.
    """
    if key is None:
        return None

    if isinstance(key, PrivateKey):
        return key.public_key()._to_proto()

    if isinstance(key, PublicKey):
        return key._to_proto()

    if isinstance(key, KeyList):
        return key._to_proto()

    if isinstance(key, ThresholdKey):
        return key._to_proto()

    raise TypeError("Key must be of type PrivateKey, PublicKey, KeyList, or ThresholdKey")


def key_from_proto(proto: basic_types_pb2.Key) -> Key:
    """
    Convert a protobuf Key message into the matching SDK key type.

    Args:
        proto (basic_types_pb2.Key): The protobuf key to convert.

    Returns:
        Key: The SDK key.

    Raises:
        ValueError: If the protobuf key variant is unsupported.
    """
    key_kind = proto.WhichOneof("key")

    if key_kind in {"ed25519", "ECDSA_secp256k1"}:
        return PublicKey._from_proto(proto)

    if key_kind == "keyList":
        return KeyList._from_proto_key_list(proto.keyList)

    if key_kind == "thresholdKey":
        return ThresholdKey._from_proto_threshold_key(proto.thresholdKey)

    raise ValueError("Unsupported key type in protobuf")


def contains_empty_key_list(key: Key | None) -> bool:
    """
    Check whether a key contains an empty KeyList anywhere in its structure.

    This catches both a top-level empty KeyList and composite keys such as a
    ThresholdKey whose child KeyList is empty.
    """
    if key is None or isinstance(key, (PrivateKey, PublicKey)):
        return False

    if isinstance(key, KeyList):
        return len(key) == 0 or any(contains_empty_key_list(child_key) for child_key in key.keys)

    if isinstance(key, ThresholdKey):
        return len(key.keys) == 0 or contains_empty_key_list(key.keys)

    raise TypeError("Key must be of type PrivateKey, PublicKey, KeyList, or ThresholdKey")

