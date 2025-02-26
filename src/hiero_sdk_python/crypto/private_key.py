from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Optional, Union
from hiero_sdk_python.crypto.public_key import PublicKey

class PrivateKey:
    """
    Represents a private key that can be either Ed25519 or ECDSA (secp256k1).
    """

    def __init__(
        self, private_key: Union[ec.EllipticCurvePrivateKey, ed25519.Ed25519PrivateKey]):
        """
        Initializes a PrivateKey from a cryptography PrivateKey object.
        """
        self._private_key = private_key

    @classmethod
    def from_string(cls, key_str: str) -> "PrivateKey":
        """
        Load a private key from a hex-encoded string.
        - If key_str starts with '0x', that prefix is removed.
        - Then the remainder is decoded as hex -> bytes.
        - Calls from_bytes to interpret raw or DER.

        Raises ValueError if the hex is invalid or the bytes are not a valid key.
        """
        key_str = key_str.removeprefix("0x")

        try:
            key_bytes = bytes.fromhex(key_str)
        except ValueError:
            raise ValueError(f"Invalid hex string for private key: {key_str}")

        return cls.from_bytes(key_bytes)

    @classmethod
    def generate(cls, key_type: str = "ed25519"):
        if key_type.lower() == "ed25519":
            return cls.generate_ed25519()
        elif key_type.lower() == "ecdsa":
            return cls.generate_ecdsa()
        else:
            raise ValueError("Invalid key_type. Use 'ed25519' or 'ecdsa'.")

    @classmethod
    def generate_ed25519(cls):
        return cls(ed25519.Ed25519PrivateKey.generate())

    @classmethod
    def generate_ecdsa(cls):
        private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        return cls(private_key)

    @classmethod
    def from_bytes(cls, key_bytes: bytes) -> "PrivateKey":
        """
        Load a private key from bytes. For Ed25519, expects 32 bytes (raw).
        For ECDSA (secp256k1), also expects 32 bytes (raw scalar).
        If the key is DER-encoded, tries to parse Ed25519 vs ECDSA.
        """
        if len(key_bytes) == 32:
            ed_priv = cls._try_load_ed25519(key_bytes)
            if ed_priv:
                return cls(ed_priv)

            ec_priv = cls._try_load_ecdsa(key_bytes)
            if ec_priv:
                return cls(ec_priv)

        der_key = cls._try_load_der(key_bytes)
        if der_key:
            return cls(der_key)

        raise ValueError("Failed to load private key from bytes.")

    @staticmethod
    def _try_load_ed25519(key_bytes: bytes) -> Optional[ed25519.Ed25519PrivateKey]:
        try:
            return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
        except Exception:
            return None

    @staticmethod
    def _try_load_ecdsa(key_bytes: bytes) -> Optional[ec.EllipticCurvePrivateKey]:
        try:
            private_int = int.from_bytes(key_bytes, "big")
            return ec.derive_private_key(private_int, ec.SECP256K1(), default_backend())
        except Exception:
            return None

    @staticmethod
    def _try_load_der(key_bytes: bytes) -> Optional[Union[ed25519.Ed25519PrivateKey, ec.EllipticCurvePrivateKey]]:
        try:
            private_key = serialization.load_der_private_key(key_bytes, password=None)
            if isinstance(private_key, ed25519.Ed25519PrivateKey):
                return private_key
            if isinstance(private_key, ec.EllipticCurvePrivateKey):
                if not isinstance(private_key.curve, ec.SECP256K1):
                    raise ValueError("Only secp256k1 ECDSA is supported.")
                return private_key
            return None
        except Exception:
            return None

    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

    def public_key(self) -> PublicKey:
        return PublicKey(self._private_key.public_key())

    def to_bytes_raw(self) -> bytes:
        if self.is_ed25519():
            return self._private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            return self._private_key.private_numbers().private_value.to_bytes(32, "big")

    def to_string(self) -> str:
        """
        Returns the private key as a hex string (raw).
        Matches old usage that calls to_string().
        """
        return self.to_string_raw()

    def to_string_raw(self) -> str:
        return self.to_bytes_raw().hex()

    def to_bytes_der(self) -> bytes:
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def to_string_der(self) -> str:
        return self.to_bytes_der().hex()

    def is_ed25519(self) -> bool:
        return isinstance(self._private_key, ed25519.Ed25519PrivateKey)

    def is_ecdsa(self) -> bool:
        return isinstance(self._private_key, ec.EllipticCurvePrivateKey)

    def __repr__(self):
        if self.is_ed25519():
            return f"<PrivateKey (Ed25519) hex={self.to_string_raw()}>"
        return f"<PrivateKey (ECDSA) hex={self.to_string_raw()}>"