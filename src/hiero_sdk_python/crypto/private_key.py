"""This module handles private key operations for ECDSA and Ed25519."""
import warnings
from typing import Optional, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.utils.crypto_utils import keccak256

_LEGACY_ECDSA_PRIVATE_KEY_PREFIX = "3030020100300706052b8104000a04220420"


class PrivateKey:
    """
    Represents a private key that can be either Ed25519 or ECDSA (secp256k1).
    Can load from raw 32-byte seeds/scalars or DER-encoded keys.
    Allows generation, signing, and public key derivation.
    """

    def __init__(
        self,
        private_key: Union[ec.EllipticCurvePrivateKey, ed25519.Ed25519PrivateKey]
    ) -> None:
        """
        Initializes a PrivateKey from a cryptography PrivateKey object.
        """
        self._private_key: Union[
            ec.EllipticCurvePrivateKey, ed25519.Ed25519PrivateKey
        ] = private_key

    #
    # ---------------------------------
    # Hex-string loaders
    # ---------------------------------
    #

    @classmethod
    def from_string(cls, key_str: str) -> "PrivateKey":
        """
        Catch all method.
        Load a private key from a hex-encoded string.
        - If key_str starts with '0x', that prefix is removed.
        - Then the remainder is decoded as hex -> bytes.
        - Calls from_bytes to interpret raw or DER.

        Raises ValueError if the hex is invalid or the bytes are not a valid key.

        NOTE: For 32-byte raw keys, this method defaults to Ed25519.
        For explicit control, use from_string_ed25519(), from_string_ecdsa(),
        or from_string_der() instead of this generic method.
        """
        key_str = key_str.removeprefix("0x")

        try:
            key_bytes = bytes.fromhex(key_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for private key: {key_str}") from exc
        return cls.from_bytes(key_bytes)

    @classmethod
    def from_string_ed25519(cls, hex_str: str) -> "PrivateKey":
        """
        Interpret the given string as hex-encoded 32-byte Ed25519 private seed.
        Specific method to aid clarity.
        """
        hex_str = hex_str.removeprefix("0x")
        try:
            key_bytes = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for Ed25519 private key: {hex_str}") from exc
        return cls.from_bytes_ed25519(key_bytes)

    @classmethod
    def from_string_ecdsa(cls, hex_str: str) -> "PrivateKey":
        """
        Interpret the given string as hex-encoded 32-byte ECDSA (secp256k1) private scalar.
        Specific method to aid clarity.
        """
        hex_str = hex_str.removeprefix("0x")
        try:
            key_bytes = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for ECDSA private key: {hex_str}") from exc
        return cls.from_bytes_ecdsa(key_bytes)

    @classmethod
    def from_string_der(cls, hex_str: str) -> "PrivateKey":
        """
        Interpret the given string as hex-encoded DER data.
        Specific method to aid clarity.
        """
        hex_str = hex_str.removeprefix("0x")
        try:
            der_data = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for DER private key: {hex_str}") from exc
        return cls.from_der(der_data)

    #
    # ---------------------------------
    # Generation
    # ---------------------------------
    #

    @classmethod
    def generate(cls, key_type: str = "ed25519") -> "PrivateKey":
        """
        Generate a new private key, defaulting to ed25519. key_type can be "ed25519" or "ecdsa".
        """
        if key_type.lower() == "ed25519":
            return cls.generate_ed25519()
        if key_type.lower() == "ecdsa":
            return cls.generate_ecdsa()
        raise ValueError("Invalid key_type. Use 'ed25519' or 'ecdsa'.")

    @classmethod
    def generate_ed25519(cls) -> "PrivateKey":
        """
        Generate a new Ed25519 private key.
        """
        return cls(ed25519.Ed25519PrivateKey.generate())

    @classmethod
    def generate_ecdsa(cls) -> "PrivateKey":
        """
        Generate a new ECDSA (secp256k1) private key.
        """
        private_key = ec.generate_private_key(ec.SECP256K1())
        return cls(private_key)

    #
    # ---------------------------------
    # Binary loaders: from_bytes, from_bytes_ed25519, from_bytes_ecdsa, from_der
    # ---------------------------------
    #

    @classmethod
    def from_bytes(cls, key_bytes: bytes) -> "PrivateKey":
        """
        Attempt to load a private key from:
          - 32-byte Ed25519 seed
          - 32-byte ECDSA scalar
          - DER-encoded private key
        """
        # If exactly 32 bytes, we have an ambiguity. Let's try Ed25519, then ECDSA, then DER.
        if len(key_bytes) == 32:
            warnings.warn(
                "from_bytes() will try Ed25519 (seed) first, then ECDSA, then DER. "
                "If your data is 32 bytes, there's no guaranteed way to distinguish which type. "
                "Consider using from_bytes_ed25519() or from_bytes_ecdsa() for clarity.",
                UserWarning,
                stacklevel=2
            )

            ed_priv = cls._try_load_ed25519(key_bytes)
            if ed_priv:
                return cls(ed_priv)

            ec_priv = cls._try_load_ecdsa(key_bytes)
            if ec_priv:
                return cls(ec_priv)

        # If not 32 bytes or attempts above failed, try DER
        der_key = cls._try_load_der(key_bytes)
        if der_key:
            return cls(der_key)

        # If all attempts failed, raise an error
        raise ValueError(
            "Failed to load private key from bytes (not Ed25519 seed, ECDSA scalar, or valid DER)."
        )

    @staticmethod
    def _try_load_ed25519(key_bytes: bytes) -> Optional[ed25519.Ed25519PrivateKey]:
        """
        Attempt to interpret the given 32 bytes as an Ed25519 private seed.
        Return the key object on success, or None on failure.
        """
        try:
            return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
        except Exception:
            return None

    @staticmethod
    def _try_load_ecdsa(key_bytes: bytes) -> Optional[ec.EllipticCurvePrivateKey]:
        """
        Attempt to interpret the given 32 bytes as an ECDSA (secp256k1) private scalar.
        Return the key object on success, or None on failure.
        """
        try:
            private_int = int.from_bytes(key_bytes, "big")
            if private_int == 0:
                return None
            return ec.derive_private_key(private_int, ec.SECP256K1())
        except Exception:
            return None

    @staticmethod
    def _try_load_der(key_bytes: bytes) -> Optional[Union[
        ed25519.Ed25519PrivateKey, ec.EllipticCurvePrivateKey
    ]]:
        """
        Attempt to parse the bytes as a DER-encoded private key.
        Auto-detect Ed25519 vs. ECDSA(secp256k1). Return None on failure.
        """
        # Try to parse the key as a legacy ECDSA key first
        try:
            return PrivateKey._parse_legacy_ecdsa_der_key(key_bytes)
        except Exception:
            pass

        try:
            private_key = serialization.load_der_private_key(key_bytes, password=None)
            # Check Ed25519
            if isinstance(private_key, ed25519.Ed25519PrivateKey):
                return private_key
            # Check ECDSA (secp256k1 only)
            if isinstance(private_key, ec.EllipticCurvePrivateKey):
                if isinstance(private_key.curve, ec.SECP256K1):
                    return private_key
            return None
        except Exception:
            return None

    @classmethod
    def from_bytes_ed25519(cls, seed_32: bytes) -> "PrivateKey":
        """
        Interpret 32 bytes as an Ed25519 seed.
        """
        if len(seed_32) != 32:
            raise ValueError("Ed25519 private key seed must be 32 bytes.")
        try:
            return cls(ed25519.Ed25519PrivateKey.from_private_bytes(seed_32))
        except Exception as e:
            raise ValueError(f"Could not load Ed25519 private key from seed: {e}") from e

    @classmethod
    def from_bytes_ecdsa(cls, scalar_32: bytes) -> "PrivateKey":
        """
        Interpret 32 bytes as an ECDSA secp256k1 private scalar.
        """
        if len(scalar_32) != 32:
            raise ValueError("ECDSA private key scalar must be 32 bytes.")
        try:
            private_int = int.from_bytes(scalar_32, "big")
            if private_int == 0:
                raise ValueError("ECDSA private key scalar cannot be zero.")

            ec_priv = ec.derive_private_key(private_int, ec.SECP256K1())
            return cls(ec_priv)
        except Exception as e:
            raise ValueError(f"Could not load ECDSA private key from scalar: {e}") from e

    @classmethod
    def from_der(cls, der_data: bytes) -> "PrivateKey":
        """
        Interpret bytes as a DER-encoded private key.
        Auto-detect Ed25519 vs. ECDSA(secp256k1).
        """
        # Try to parse the key as a legacy ECDSA key first
        try:
            private_key = PrivateKey._parse_legacy_ecdsa_der_key(der_data)
            return cls(private_key)
        except Exception:
            pass

        try:
            private_key = serialization.load_der_private_key(der_data, password=None)
        except Exception as e:
            raise ValueError(f"Could not parse DER private key: {e}") from e

        if isinstance(private_key, ed25519.Ed25519PrivateKey):
            return cls(private_key)

        if isinstance(private_key, ec.EllipticCurvePrivateKey):
            if not isinstance(private_key.curve, ec.SECP256K1):
                raise ValueError("Only secp256k1 ECDSA is supported.")
            return cls(private_key)

        raise ValueError("Unsupported private key type (not Ed25519 or secp256k1).")

    #
    # ---------------------------------
    # Signatures and Public Key
    # ---------------------------------
    #
    def sign(self, data: bytes) -> bytes:
        """
        Sign the given data using this private key.

        - If Ed25519, the signature is produced using Ed25519's library.
        - If ECDSA (secp256k1), the signature uses ECDSA with SHA-256.
        """
        if isinstance(self._private_key, ed25519.Ed25519PrivateKey):
            # Ed25519 automatically handles the hashing internally
            return self._private_key.sign(data)
        
        data_hash = keccak256(data)
        signature_der = self._private_key.sign(data_hash, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256())))
        r, s = asym_utils.decode_dss_signature(signature_der)
        signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return signature

    def public_key(self) -> PublicKey:
        """
        Derive the public key from this private key.
        """
        return PublicKey(self._private_key.public_key())


    #
    # ---------------------------------
    # Serialization
    # ---------------------------------
    #

    def to_bytes_raw(self) -> bytes:
        """
        Return the raw 32-byte seed (Ed25519) or 32-byte scalar (ECDSA).
        """
        if self.is_ed25519():
            return self.to_bytes_ed25519_raw()
        if self.is_ecdsa():
            return self.to_bytes_ecdsa_raw()
        raise ValueError("Unknown key type; cannot extract raw bytes.")

    def to_bytes_ed25519_raw(self) -> bytes:
        """
        Return the raw 32-byte Ed25519 seed.
        """
        if not self.is_ed25519():
            raise ValueError("Not an Ed25519 key.")
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def to_bytes_ecdsa_raw(self) -> bytes:
        """
        Return the raw 32-byte ECDSA (secp256k1) scalar.
        """
        if not isinstance(self._private_key, ec.EllipticCurvePrivateKey):
            raise TypeError("Not an ECDSA (secp256k1) key.")

        return self._private_key.private_numbers()\
                   .private_value.to_bytes(32, "big")

    def to_bytes_der(self) -> bytes:
        """
        Return the DER-encoded private key.
        """
        if self.is_ed25519():
            # Ed25519 only supports PKCS#8 for DER exports
            return self._private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        # ECDSA can be exported in Traditional OpenSSL or PKCS#8
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
            )

    def to_string_raw(self) -> str:
        """
        Returns the private key as a hex string (raw).
        """
        return self.to_bytes_raw().hex()

    def to_string_ed25519_raw(self) -> str:
        """
        Returns the Ed25519 private key as a hex string (raw).
        """
        return self.to_bytes_ed25519_raw().hex()

    def to_string_ecdsa_raw(self) -> str:
        """
        Returns the ECDSA private key as a hex string (raw).
        """
        return self.to_bytes_ecdsa_raw().hex()

    def to_string_der(self) -> str:
        """
        Returns the DER-encoded private key as a hex string.
        """
        return self.to_bytes_der().hex()

    def to_string(self) -> str:
        """
        Returns the private key as a hex string (raw).
        Matches old usage that calls to_string().
        """
        return self.to_string_raw()
    #
    # ---------------------------------
    # is_ed25519 / is_ecdsa checks
    # ---------------------------------
    #

    def is_ed25519(self) -> bool:
        """
        Check if this private key is Ed25519.
        Returns True if it is an Ed25519 private key, False otherwise.
        """
        return isinstance(self._private_key, ed25519.Ed25519PrivateKey)

    def is_ecdsa(self) -> bool:
        """
        Check if this private key is ECDSA.
        Returns True if it is an ECDSA private key, False otherwise.
        """
        return isinstance(self._private_key, ec.EllipticCurvePrivateKey)

    def __repr__(self) -> str:
        if self.is_ed25519():
            return f"<PrivateKey (Ed25519) hex={self.to_string_raw()}>"
        return f"<PrivateKey (ECDSA) hex={self.to_string_raw()}>"

    #
    # ---------------------------------
    # Helper methods
    # ---------------------------------
    #
    @staticmethod
    def _parse_legacy_ecdsa_der_key(key_bytes: bytes) -> "ec.EllipticCurvePrivateKey":
        """
        Parse a legacy ECDSA private key from DER-encoded bytes.

        Legacy keys have a specific prefix that needs to be removed before parsing.

        Args:
            key_bytes: DER-encoded bytes containing the legacy ECDSA private key

        Returns:
            EllipticCurvePrivateKey: The parsed ECDSA private key

        Raises:
            ValueError: If the key format is invalid or parsing fails
        """
        if not key_bytes.hex().startswith(_LEGACY_ECDSA_PRIVATE_KEY_PREFIX):
            raise ValueError("Missing legacy ECDSA prefix")

        # Remove the legacy prefix
        hex_without_prefix = key_bytes.hex().removeprefix(
            _LEGACY_ECDSA_PRIVATE_KEY_PREFIX
        )

        try:
            raw_key_bytes = bytes.fromhex(hex_without_prefix)
        except ValueError as exc:
            raise ValueError("Invalid hex data after prefix removal") from exc

        # ECDSA private keys must be exactly 32 bytes
        if len(raw_key_bytes) != 32:
            raise ValueError(
                f"Invalid key length: {len(raw_key_bytes)} bytes (expected 32)"
            )

        private_int = int.from_bytes(raw_key_bytes, "big")

        if private_int == 0:
            raise ValueError("ECDSA private key scalar cannot be zero")

        try:
            return ec.derive_private_key(private_int, ec.SECP256K1())
        except Exception as exc:
            raise ValueError(f"Failed to derive ECDSA private key: {exc}") from exc
