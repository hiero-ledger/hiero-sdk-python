from typing import Union
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey


class Key:
    """
    A unified wrapper around PrivateKey and PublicKey.
    Provides a common interface for working with both key types.
    """

    def __init__(self, key: Union[PrivateKey, PublicKey]):
        """
        Initialize a Key with either a PrivateKey or PublicKey.
        
        Args:
            key: Either a PrivateKey or PublicKey instance
        """
        self._key = key

    @classmethod
    def from_string(cls, key_str: str) -> "Key":
        """
        Parse a string into a Key.
        
        Attempts to parse as a PrivateKey first, then falls back to PublicKey.
        
        Args:
            key_str: Hex-encoded key string
            
        Returns:
            Key: A new Key instance
            
        Raises:
            ValueError: If the string cannot be parsed as either key type
        """
        # Try to parse as private key first
        try:
            private_key = PrivateKey.from_string(key_str)
            return cls(private_key)
        except (ValueError, Exception):
            pass
        
        # Fall back to public key
        try:
            public_key = PublicKey.from_string(key_str)
            return cls(public_key)
        except (ValueError, Exception) as e:
            raise ValueError(f"Could not parse key string as either private or public key: {e}") from e

    def to_string(self) -> str:
        """
        Returns the key as a hex-encoded string.
        
        Returns:
            str: Hex-encoded representation of the key
        """
        return self._key.to_string()

    @property
    def is_private(self) -> bool:
        """
        Check if this is a private key.
        
        Returns:
            bool: True if the key is a private key, False otherwise
        """
        return isinstance(self._key, PrivateKey)

    @property
    def is_public(self) -> bool:
        """
        Check if this is a public key.
        
        Returns:
            bool: True if the key is a public key, False otherwise
        """
        return isinstance(self._key, PublicKey)

    @property
    def public_key(self) -> PublicKey:
        """
        Get the public key.
        
        If this Key wraps a PrivateKey, derives the public key.
        If this Key wraps a PublicKey, returns it directly.
        
        Returns:
            PublicKey: The public key
        """
        if self.is_private:
            return self._key.public_key()
        return self._key

    @property
    def private_key(self) -> PrivateKey:
        """
        Get the private key.
        
        Returns:
            PrivateKey: The private key
            
        Raises:
            ValueError: If this Key wraps a PublicKey (cannot derive private from public)
        """
        if not self.is_private:
            raise ValueError("Key is not a private key")
        return self._key

