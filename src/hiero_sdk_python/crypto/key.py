"""This module provides a unified Key class that can represent both private and public keys."""
from typing import Union
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey


class Key:
    """
    Represents either a PrivateKey or a PublicKey.
    
    This unified class provides a common interface for key operations,
    making it easier to work with keys without needing to know the specific type.
    
    Benefits:
    - Unified API for easier use
    - Less code duplication
    - Safer key handling
    - Easier future extensions
    """

    def __init__(self, key: Union[PrivateKey, PublicKey]) -> None:
        """
        Initialize a Key with either a PrivateKey or PublicKey.
        
        Args:
            key: Either a PrivateKey or PublicKey instance
            
        Raises:
            ValueError: If key is not a PrivateKey or PublicKey instance
        """
        if not isinstance(key, (PrivateKey, PublicKey)):
            raise ValueError("Key must be either a PrivateKey or PublicKey instance")
        self._key = key

    @classmethod
    def from_string(cls, key_str: str) -> "Key":
        """
        Parse a string into a Key object.
        
        This method attempts to parse the string as both a private key and public key.
        Due to ambiguity with Ed25519 keys (both private seeds and public keys are 32 bytes),
        this method defaults to private key interpretation for 32-byte hex strings.
        
        For unambiguous parsing, use the specific key type methods:
        - PrivateKey.from_string() for private keys
        - PublicKey.from_string() for public keys
        
        Args:
            key_str: Hex-encoded key string (with or without '0x' prefix)
            
        Returns:
            Key: A new Key instance
            
        Raises:
            ValueError: If the string cannot be parsed as either key type
        """
        key_str = key_str.removeprefix("0x")
        
        try:
            key_bytes = bytes.fromhex(key_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string: {key_str}") from exc
        
        # For 32-byte keys, there's ambiguity between Ed25519 private/public keys
        # Try private key first (more common use case)
        if len(key_bytes) == 32:
            try:
                private_key = PrivateKey.from_string(key_str)
                return cls(private_key)
            except ValueError:
                pass
        
        # For non-32-byte keys or if private key parsing failed, try other types
        try:
            private_key = PrivateKey.from_string(key_str)
            return cls(private_key)
        except ValueError:
            pass
        
        # Try public key as fallback
        try:
            public_key = PublicKey.from_string(key_str)
            return cls(public_key)
        except ValueError:
            pass
        
        raise ValueError(f"Could not parse string as either private or public key: {key_str}")

    @property
    def is_private(self) -> bool:
        """
        Check if this key is a private key.
        
        Returns:
            bool: True if this is a private key, False otherwise
        """
        return isinstance(self._key, PrivateKey)

    @property
    def is_public(self) -> bool:
        """
        Check if this key is a public key.
        
        Returns:
            bool: True if this is a public key, False otherwise
        """
        return isinstance(self._key, PublicKey)

    def public_key(self) -> PublicKey:
        """
        Get the public key.
        
        If this Key wraps a PrivateKey, derives the public key from it.
        If this Key wraps a PublicKey, returns it directly.
        
        Returns:
            PublicKey: The public key
        """
        if isinstance(self._key, PrivateKey):
            return self._key.public_key()
        return self._key

    def private_key(self) -> PrivateKey:
        """
        Get the private key.
        
        Returns:
            PrivateKey: The private key
            
        Raises:
            ValueError: If this Key wraps a PublicKey (no private key available)
        """
        if isinstance(self._key, PublicKey):
            raise ValueError("Cannot extract private key from a public key")
        return self._key

    def sign(self, data: bytes) -> bytes:
        """
        Sign data with this key.
        
        Args:
            data: The data to sign
            
        Returns:
            bytes: The signature
            
        Raises:
            ValueError: If this Key wraps a PublicKey (cannot sign with public key)
        """
        if isinstance(self._key, PublicKey):
            raise ValueError("Cannot sign with a public key")
        return self._key.sign(data)

    def verify(self, signature: bytes, data: bytes) -> None:
        """
        Verify a signature against data using this key's public key.
        
        Args:
            signature: The signature to verify
            data: The original data that was signed
            
        Raises:
            InvalidSignature: If the signature is invalid
        """
        public_key = self.public_key()
        public_key.verify(signature, data)

    def __repr__(self) -> str:
        """
        Return a string representation of the Key.
        
        Returns:
            str: String representation showing key type and hex value
        """
        key_type = "Private" if self.is_private else "Public"
        return f"<Key ({key_type}) {repr(self._key)}>"
