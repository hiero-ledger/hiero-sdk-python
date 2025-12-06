"""
hiero_sdk_python.utils.key_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions and type definitions for working with cryptographic keys.
"""

from typing import Optional, Union

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2

# Type alias for keys that can be either PrivateKey or PublicKey
Key = Union[PrivateKey, PublicKey]


def key_to_proto(key: Optional[Key]) -> Optional[basic_types_pb2.Key]:
    """
    Helper function to convert a key (PrivateKey or PublicKey) to protobuf Key format.

    This function handles the conversion of SDK key types to protobuf format:
    - If a PrivateKey is provided, its corresponding public key is extracted and converted.
    - If a PublicKey is provided, it is converted directly to protobuf.
    - If None is provided, None is returned.

    Args:
        key (Optional[Key]): The key to convert (PrivateKey or PublicKey), or None
            
    Returns:
        basic_types_pb2.Key (Optional): The protobuf key or None if key is None
        
    Raises:
        TypeError: If the provided key is not a PrivateKey, PublicKey, or None.
    """
    if not key:
        return None

    # If it's a PrivateKey, get the public key first, then convert to proto
    if isinstance(key, PrivateKey):
        return key.public_key()._to_proto()
    
    # If it's a PublicKey, convert directly to proto
    if isinstance(key, PublicKey):
        return key._to_proto()

    # Safety net: This will fail if a non-key is passed
    raise TypeError("Key must be of type PrivateKey or PublicKey")

