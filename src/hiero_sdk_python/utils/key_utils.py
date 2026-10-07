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


def normalize_keys(keys: Key | list[Key] | tuple[Key, ...] | None) -> list[Key] | None:
    """
    Normalize a keys argument to a list of Key objects, or None.

    A single Key becomes a one-element list; a tuple of keys becomes a list.
    None is returned unchanged so callers can distinguish "not set" from
    "explicitly empty".

    Args:
        keys (Key | list[Key] | tuple[Key, ...] | None): The keys to normalize.

    Returns:
        Optional[list[Key]]: The normalized list of keys, or None.

    Raises:
        TypeError: If keys is not a Key, a list/tuple of Key objects, or None.
    """
    if keys is None:
        return None

    if isinstance(keys, Key):
        return [keys]

    if isinstance(keys, tuple):
        keys = list(keys)

    if not isinstance(keys, list) or not all(isinstance(key, Key) for key in keys):
        raise TypeError("keys must be a Key, list of Key objects, or None")

    return keys
