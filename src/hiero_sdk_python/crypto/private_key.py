from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from hiero_sdk_python.crypto.public_key import PublicKey


class PrivateKey:
    """
    Represents a private key that can be either Ed25519 or ECDSA (secp256k1).
    """

    def __init__(self, private_key):
        """
        Initializes a PrivateKey from a cryptography PrivateKey object.
        """
        self._private_key = private_key

    @classmethod
    def generate(cls, key_type: str = "ed25519"):
        """
        Generates a new private key. Defaults to an Ed25519 private key unless
        'ecdsa' is specified.

        Args:
            key_type (str): Either 'ed25519' or 'ecdsa'. Defaults to 'ed25519'.

        Returns:
            PrivateKey: A new instance of PrivateKey.
        """
        if key_type.lower() == "ed25519":
            return cls.generate_ed25519()
        elif key_type.lower() == "ecdsa":
            return cls.generate_ecdsa()
        else:
            raise ValueError("Invalid key_type. Use 'ed25519' or 'ecdsa'.")

    @classmethod
    def generate_ed25519(cls):
        """
        Generates a new Ed25519 private key.

        Returns:
            PrivateKey: A new instance of PrivateKey using Ed25519.
        """
        return cls(ed25519.Ed25519PrivateKey.generate())

    @classmethod
    def generate_ecdsa(cls):
        """
        Generates a new ECDSA (secp256k1) private key.

        Returns:
            PrivateKey: A new instance of PrivateKey using ECDSA.
        """
        private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        return cls(private_key)

    @classmethod
    def from_bytes(cls, key_bytes: bytes):
        """
        Load a private key from bytes. For Ed25519, expects 32 bytes.
        For ECDSA (secp256k1), also expects 32 bytes (raw scalar).
        If the key is DER-encoded, tries to parse and detect Ed25519 vs ECDSA.

        Args:
            key_bytes (bytes): Private key bytes.

        Returns:
            PrivateKey: A new instance of PrivateKey.

        Raises:
            ValueError: If the key is invalid or unsupported.
        """
        if len(key_bytes) == 32:
            try:
                ed_priv = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
                return cls(ed_priv)
            except Exception:
                pass
            try:
                private_int = int.from_bytes(key_bytes, "big")
                ec_priv = ec.derive_private_key(private_int, ec.SECP256K1(), default_backend())
                return cls(ec_priv)
            except Exception:
                pass

        try:
            private_key = serialization.load_der_private_key(key_bytes, password=None)
        except Exception as e:
            raise ValueError(f"Failed to load private key (DER): {e}")

        if isinstance(private_key, ed25519.Ed25519PrivateKey):
            return cls(private_key)

        if isinstance(private_key, ec.EllipticCurvePrivateKey):
            if not isinstance(private_key.curve, ec.SECP256K1):
                raise ValueError("Only secp256k1 ECDSA is supported.")
            return cls(private_key)

        raise ValueError("Unsupported private key type.")

    @classmethod
    def from_string(cls, key_str):
        """
        Load a private key from a hex-encoded string. For Ed25519, expects 32 bytes.
        For ECDSA (secp256k1), also expects 32 bytes (raw scalar).
        If the key is DER-encoded, tries to parse and detect Ed25519 vs ECDSA.

        Args:
            key_str (str): The hex-encoded private key string.

        Returns:
            PrivateKey: A new instance of PrivateKey.

        Raises:
            ValueError: If the key is invalid or unsupported.
        """
        try:
            key_bytes = bytes.fromhex(key_str.removeprefix("0x"))
        except ValueError:
            raise ValueError("Invalid hex-encoded private key string.")

        return cls.from_bytes(key_bytes)

    def sign(self, data: bytes) -> bytes:
        """
        Signs the given data using this private key (Ed25519 or ECDSA).

        Args:
            data (bytes): The data to sign.

        Returns:
            bytes: The signature.
        """
        return self._private_key.sign(data)

    def public_key(self) -> PublicKey:
        """
        Retrieves the corresponding PublicKey.

        Returns:
            PublicKey: The public key associated with this private key.
        """
        return PublicKey(self._private_key.public_key())

    def to_bytes_raw(self) -> bytes:
        """
        Returns the private key bytes in raw form (32 bytes for both Ed25519 and ECDSA).

        Returns:
            bytes: The raw private key bytes.
        """
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

    def to_string_raw(self) -> str:
        """
        Returns the raw private key as a hex-encoded string.

        Returns:
            str: The hex-encoded raw private key.
        """
        return self.to_bytes_raw().hex()
    
    def to_string(self) -> str:
        """
        Returns the private key as a hex string (raw).
        """
        return self.to_string_raw()

    def is_ed25519(self) -> bool:
        """
        Checks if this private key is Ed25519.

        Returns:
            bool: True if Ed25519, False otherwise.
        """
        return isinstance(self._private_key, ed25519.Ed25519PrivateKey)

    def is_ecdsa(self) -> bool:
        """
        Checks if this private key is ECDSA (secp256k1).

        Returns:
            bool: True if ECDSA, False otherwise.
        """
        from cryptography.hazmat.primitives.asymmetric import ec
        return isinstance(self._private_key, ec.EllipticCurvePrivateKey)

    def __repr__(self):
        if self.is_ed25519():
            return f"<PrivateKey (Ed25519) hex={self.to_string_raw()}>"
        return f"<PrivateKey (ECDSA) hex={self.to_string_raw()}>"
