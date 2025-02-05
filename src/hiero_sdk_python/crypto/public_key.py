from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization

class PublicKey:
    """
    Represents a public key that can be either Ed25519 or ECDSA (secp256k1).
    """

    def __init__(self, public_key):
        """
        Initializes a PublicKey from a cryptography PublicKey object.
        """
        self._public_key = public_key

    @classmethod
    def from_bytes(cls, key_bytes: bytes):
        """
        Load a public key from bytes.
        For Ed25519, expects 32 bytes. Raw bytes for ECDSA are not supported for now.
        If the key is DER-encoded, tries to parse and detect Ed25519 vs ECDSA.

        Args:
            key_bytes (bytes): Public key bytes.

        Returns:
            PublicKey: A new instance of PublicKey.

        Raises:
            ValueError: If the key is invalid or unsupported.
        """

        if len(key_bytes) == 32:
            ed_public = ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
            return cls(ed_public)
        # TODO: Consider adding support for creating ECDSA public key instance from raw encoded point
        # Java SDK example: https://github.com/hiero-ledger/hiero-sdk-java/blob/main/sdk-java/src/main/java/org/hiero/sdk/java/PublicKeyECDSA.java#L46
        #
        # Potential approach for Python:
        # ec_public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), key_bytes)

        try:
            public_key = serialization.load_der_public_key(key_bytes)
        except Exception as e:
            raise ValueError(f"Failed to load public key (DER): {e}")

        if isinstance(public_key, ed25519.Ed25519PublicKey):
            return cls(public_key)

        if isinstance(public_key, ec.EllipticCurvePublicKey):
            if not isinstance(public_key.curve, ec.SECP256K1):
                raise ValueError("Only secp256k1 ECDSA is supported.")
            return cls(public_key)

        raise ValueError("Unsupported public key type.")

    @classmethod
    def from_string(cls, key_str):
        """
        Load a public key from a hex-encoded string.
        For Ed25519, expects 32 bytes. Raw bytes string for ECDSA is not supported for now.
        If the key is DER-encoded, tries to parse and detect Ed25519 vs ECDSA.

        Args:
            key_str (str): The hex-encoded public key string.

        Returns:
            PublicKey: A new instance of PublicKey.

        Raises:
            ValueError: If the key is invalid or unsupported.
        """
        try:
            key_bytes = bytes.fromhex(key_str.removeprefix("0x"))
        except ValueError:
            raise ValueError("Invalid hex-encoded public key string.")

        return cls.from_bytes(key_bytes)

    def verify(self, signature: bytes, data: bytes) -> None:
        """
        Verifies a signature for the given data using this public key.
        Raises an exception if the signature is invalid.

        Args:
            signature (bytes): The signature to verify.
            data (bytes): The data that was signed.

        Raises:
            cryptography.exceptions.InvalidSignature: If the signature is invalid.
        """
        self._public_key.verify(signature, data)

    def to_bytes_raw(self) -> bytes:
        """
        Returns the public key in raw form:
         - For Ed25519, it's 32 bytes.
         - For ECDSA (secp256k1), it's the uncompressed or compressed form, 
           depending on how cryptography outputs RAW. Usually 33 bytes compressed.

        Returns:
            bytes: The raw public key bytes.
        """
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def to_string_raw(self) -> str:
        """
        Returns the raw public key as a hex-encoded string.

        Returns:
            str: The hex-encoded raw public key.
        """
        return self.to_bytes_raw().hex()
    
    def to_string(self) -> str:
        """
        Returns the private key as a hex string (raw).
        """
        return self.to_string_raw()


    def is_ed25519(self) -> bool:
        """
        Checks if this public key is Ed25519.

        Returns:
            bool: True if Ed25519, False otherwise.
        """
        return isinstance(self._public_key, ed25519.Ed25519PublicKey)

    def is_ecdsa(self) -> bool:
        """
        Checks if this public key is ECDSA (secp256k1).

        Returns:
            bool: True if ECDSA, False otherwise.
        """
        return isinstance(self._public_key, ec.EllipticCurvePublicKey)

    def to_proto(self):
        """
        Returns the protobuf representation of the public key.
        For Ed25519, uses the 'ed25519' field in Key.
        For ECDSA, uses the 'ECDSASecp256k1' field (may differ by your actual Hedera environment).

        Returns:
            Key: The protobuf Key message.
        """
        from hiero_sdk_python.hapi.services import basic_types_pb2

        pub_bytes = self.to_bytes_raw()
        if self.is_ed25519():
            return basic_types_pb2.Key(ed25519=pub_bytes)
        else:
            return basic_types_pb2.Key(ECDSASecp256k1=pub_bytes)

    def __repr__(self):
        if self.is_ed25519():
            return f"<PublicKey (Ed25519) hex={self.to_string_raw()}>"
        return f"<PublicKey (ECDSA) hex={self.to_string_raw()}>"
