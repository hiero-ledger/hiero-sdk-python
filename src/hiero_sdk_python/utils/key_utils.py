"""
hiero_sdk_python.utils.key_utils.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions and type definitions for working with cryptographic keys.
"""

from __future__ import annotations

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services import basic_types_pb2


def key_to_proto(key: Key | None) -> basic_types_pb2.Key | None:
    """
    Helper function to convert an SDK key to protobuf Key format.

    This function handles any concrete subclass of Key by delegating to its
    to_proto_key() implementation. If None is provided, None is returned.

    Args:
        key (Optional[Key]): The key to convert, or None

    Returns:
        basic_types_pb2.Key (Optional): The protobuf key or None if key is None

    Raises:
        TypeError: If the provided key is not a Key instance or None.
    """
    if key is None:
        return None

    if isinstance(key, Key):
        return key.to_proto_key()

    raise TypeError("Key must be of type PrivateKey or PublicKey, or another SDK Key implementation")
