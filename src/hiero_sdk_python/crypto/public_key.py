"""This module handles Public key operations"""
import warnings
from typing import Union

from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.crypto_utils import keccak256

def _warn_ed25519_ambiguity(caller_name: str) -> None:
    warnings.warn(
        f"{caller_name}: cannot distinguish Ed25519 private seeds from public keys. "
        "If using Ed25519, ensure you truly have a public key.",
        UserWarning,
        stacklevel=3
    )

class PublicKey:
    """
    Represents a public key.
    Supports multiple key formats: raw bytes, DER-encoded keys,
    hex strings, and a protobuf (“proto”) representation.
    
    """

    def __init__(
        self,
        public_key: Union[ec.EllipticCurvePublicKey, ed25519.Ed25519PublicKey]
    ) -> None:
        """
        Initializes a PublicKey from a cryptography PublicKey object.
        """
        self._public_key: Union[ec.EllipticCurvePublicKey, ed25519.Ed25519PublicKey] = public_key

    #
    # ---------------------------------
    # Type-specific (Ed25519, ECDSA secp256k1, DER) from bytes loaders.
    # Designed to help the user correctly manage key types.
    # These are functionaly identical to the catch-all from_bytes method below.
    # ---------------------------------
    #

    @classmethod
    def from_bytes(cls, pub: bytes) -> "PublicKey":
        """
        Catch-all method to load public keys from bytes (Ed25519, ECDSA, or DER).
        """
        _warn_ed25519_ambiguity("PublicKey.from_bytes")

        # 1) 32-byte raw ⇒ Ed25519
        if len(pub) == 32:
            return cls._from_bytes_ed25519(pub)

        # 2) 33/65 bytes ⇒ ECDSA (secp256k1)
        if len(pub) in (33, 65):
            return cls.from_bytes_ecdsa(pub)

        # 3) Otherwise ⇒ DER, but wrap any failure
        try:
            return cls.from_der(pub)
        except ValueError as exc:
            raise ValueError("Failed to load public key") from exc

    @classmethod
    def from_bytes_ed25519(cls, pub: bytes) -> "PublicKey":
        """
        Load an Ed25519 public key from public raw bytes.

        Args:
            pub (bytes): 32-byte raw Ed25519 public key point.

        Returns:
            PublicKey: A new instance wrapping the validated public key.

        Raises:
            ValueError: If `pub` is not exactly 32 bytes or fails point validation.
        """
        _warn_ed25519_ambiguity("PublicKey.from_bytes_ed25519")

        return cls._from_bytes_ed25519(pub)

    @classmethod
    def _from_bytes_ed25519(cls, pub: bytes) -> "PublicKey":
        """
        Load an Ed25519 public key from public raw bytes.

        Args:
            pub (bytes): 32-byte raw Ed25519 public key point.

        Returns:
            PublicKey: A new instance wrapping the validated public key.

        Raises:
            ValueError: If `pub` is not exactly 32 bytes or fails point validation.
        """
        # 1) Enforce exact length for raw Ed25519 keys which are 32 bytes.
        if len(pub) != 32:
            raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(pub)}.")

        # 2) Delegate to ed25519 cryptography library for curve-point validation
        try:
            ed_pub = ed25519.Ed25519PublicKey.from_public_bytes(pub)
        except Exception as e:
            # Error raised if bytes do not form a valid Ed25519 public point
            raise ValueError(f"Invalid Ed25519 public key bytes: {e}") from e
        # 3) Return the validated public key
        return cls(ed_pub)


    @classmethod
    def from_bytes_ecdsa(cls, pub: bytes) -> "PublicKey":
        """
        Load a secp256k1 ECDSA public key from raw bytes.

        This method accepts only properly encoded public-key points:
          - Compressed: 33 bytes, prefix 0x02 or 0x03.
          - Uncompressed: 65 bytes, prefix 0x04.

        Note:
          - ECDSA private keys are 32-byte scalars and will be rejected.

        Args:
            pub (bytes): Raw public-key point in compressed or uncompressed form.

        Returns:
            PublicKey: Wrapped ECDSA (secp256k1) public key.

        Raises:
            ValueError: If length is not 33 or 65 bytes, or if point validation fails.
        """
        # 1) Enforce valid public bytes point lengths
        # (does not allow private-key scalars which are 32 bytes)
        if len(pub) not in (33, 65):
            raise ValueError(
                f"ECDSA (secp256k1) public key must be 33 or 65 bytes, got {len(pub)}."
            )

        # 2) Delegate to cryptography ec library for point decoding and validation
        try:
            ec_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pub)
        except Exception as e:
            # Raised if bytes do not correspond to a valid curve point
            raise ValueError(f"Invalid ECDSA public key bytes: {e}") from e

        # 3) Wrap and return
        return cls(ec_pub)

    @classmethod
    def from_der(cls, der_bytes: bytes) -> "PublicKey":
        """
        Load a public key from DER-encoded SubjectPublicKeyInfo.

        This method automatically detects Ed25519 vs. secp256k1 ECDSA 
        based on the OID found in the DER bytes. It strictly expects 
        a DER-encoded **public** key (SubjectPublicKeyInfo).
        
        The `cryptography` library's `load_der_public_key` function 
        rejects DER-encoded private keys, as their structure differs.

        *Warning* a ed25519 private key incorrectly passed as a public key
        and became DER-encoded will still be processed as a public key.  

        Args:
            der_bytes (bytes): DER-encoded SubjectPublicKeyInfo.

        Returns:
            PublicKey: A wrapped key of the detected algorithm 
            (Ed25519 or secp256k1 ECDSA).

        Raises:
            ValueError: If the DER bytes cannot be parsed as a public 
            key, or if the curve/algorithm is unsupported. This 
            includes cases where a private key is passed instead of a 
            public key.
        """
        try:
            maybe_pub = serialization.load_der_public_key(der_bytes)
        except Exception as e:
            raise ValueError(f"Could not parse DER public key: {e}") from e

        # If its Ed25519, delegate to cryptography Ed25519 library for point decoding and validation
        # *Watch out!* Incorrectly passed private Ed25519 keys into DER will be treated as public.
        if isinstance(maybe_pub, ed25519.Ed25519PublicKey):
            return cls(maybe_pub)
        # If its ECDSA, delegate to cryptography ec library for point decoding and validation
        if isinstance(maybe_pub, ec.EllipticCurvePublicKey):
            if not isinstance(maybe_pub.curve, ec.SECP256K1):
                raise ValueError("Unsupported ECDSA curve (only secp256k1 allowed)")
            return cls(maybe_pub)

        raise ValueError("Unsupported public key type in DER (not Ed25519 or secp256k1 ECDSA)")

    #
    # -----------------------------------
    # Type-specific (Ed25519, ECDSA secp256k1, DER) hex loaders.
    # The benefit is greater user clarity to enable correct key handling.
    # -----------------------------------
    #

    @classmethod
    def from_string_ed25519(cls, hex_str: str) -> "PublicKey":
        """
        Interpret the given string as a hex-encoded 32-byte Ed25519 public key.
        """
        _warn_ed25519_ambiguity("PublicKey.from_string_ed25519")

        # Sanitizing: The "0x" prefix denotes that a string represents a hex number.
        # Note: "0x" is not part of the binary or numeric value of the hex string.

        hex_str = hex_str.removeprefix("0x")
        # Python's .fromhex will throw if the hex string is malformed
        try:
            pub = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for Ed25519 public key: {hex_str!r}") from exc
        # 3) Delegate to the byte-level loader
        return cls._from_bytes_ed25519(pub)

    @classmethod
    def from_string_ecdsa(cls, hex_str: str) -> "PublicKey":
        """
        Interpret the given string as a hex-encoded compressed/uncompressed 
        ECDSA pubkey (33/65 bytes).
 
        Sanitizing. The "0x" prefix is used to denote that a string -
        represents a hexadecimal number.
        The "0x" itself isn't part of the binary or numerical 
        value represented by the hexadecimal string"""
        hex_str = hex_str.removeprefix("0x")
        try:
            # Python's .fromhex will throw if the hex string is malformed
            pub = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for ECDSA public key: {hex_str}") from exc
        return cls.from_bytes_ecdsa(pub)

    @classmethod
    def from_string_der(cls, hex_str: str) -> "PublicKey":
        """
        Interpret the given string as hex-encoded DER bytes containing a public key.
        """
        # Sanitizing. The "0x" prefix is used to denote that a string
        # represents a hexadecimal number.
        # The "0x" itself isn't part of the binary or
        # numerical value represented by the hexadecimal string
        hex_str = hex_str.removeprefix("0x")
        try:
            # Python's .fromhex will throw if the hex string is malformed
            der_bytes = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex string for DER public key: {hex_str}") from exc
        return cls.from_der(der_bytes)

    #
    # -----------------------------------
    # Catch-all (Ed25519, ECDSA secp256k1, DER) hex loaders.
    # Used for convenience assuming correct key handling.
    # -----------------------------------
    #

    @classmethod
    def from_string(cls, hex_str: str) -> "PublicKey":
        """
        Load a *public* key from a hex-encoded string. Catch-all method supporting:
        
          - Ed25519 raw (32 bytes → 64 hex chars)
          - secp256k1 ECDSA compressed (33 bytes → 66 hex chars)
          - secp256k1 ECDSA uncompressed (65 bytes → 130 hex chars)
          - DER-encoded SPKI (variable length)
        
        *Warning*: Raw Ed25519 private seeds are also 32 bytes and will be
        treated as valid public keys here.
        """
        _warn_ed25519_ambiguity("PublicKey.from_string")

        # 1) Remove the unecessary prefix and decode the hex
        hex_str = hex_str.removeprefix("0x")
        try:
            data = bytes.fromhex(hex_str)
        except ValueError as exc:
            raise ValueError(f"Invalid hex-encoded public key string: {hex_str!r}") from exc

        # 2) dispatch as ed25519 or ecdsa based on length
        n = len(data)
        if n == 32:
            # raw Ed25519
            # Warning! Incorrectly passed private ed25519 keys will be passed as public
            return cls._from_bytes_ed25519(data)
        if n in (33, 65):
            # raw secp256k1
            return cls.from_bytes_ecdsa(data)

        # 3) fallback: DER-encoded
        try:
            return cls.from_der(data)
        except ValueError as e:
            raise ValueError(f"Couldn’t parse DER public key: {e}") from e

    #
    # ---------------------------------
    # From proto
    # ---------------------------------
    #

    @classmethod
    def _from_proto(cls, proto: Key) -> "PublicKey":
        """
        Load a public key from a protobuf Key message.
        """
        if proto.ed25519:
            return cls._from_bytes_ed25519(proto.ed25519)
        if proto.ECDSA_secp256k1:
            return cls.from_bytes_ecdsa(proto.ECDSA_secp256k1)
        if proto.contractID.ByteSize() > 0:
            return ContractId._from_proto(proto.contractID)
        raise ValueError("Unsupported public key type in protobuf")

    #
    # ---------------------------------
    # To proto
    # ---------------------------------
    #

    def _to_proto(self) -> Key:
        """
        Returns the protobuf representation of the public key (key type is known).
        For Ed25519, uses the 'ed25519' field.
        For ECDSA, uses 'ECDSASecp256k1'.
        For DER, decode type first using from_der or from_bytes.

        Returns:
            Key: The protobuf Key message.
        """

        # get the raw public-key bytes (32/33/65 bytes depending on type)
        pub_bytes = self.to_bytes_raw()

        if self.is_ed25519():
            return basic_types_pb2.Key(ed25519=pub_bytes)
        return basic_types_pb2.Key(ECDSA_secp256k1=pub_bytes)

    #
    # ---------------------------------
    # Utilities
    # ---------------------------------
    #

    def is_ed25519(self) -> bool:
        """
        Checks if this key (private or public) is Ed25519.
        """
        return isinstance(self._public_key, ed25519.Ed25519PublicKey)

    def is_ecdsa(self) -> bool:
        """
        Checks if this public key is ECDSA (secp256k1).
        """
        return isinstance(self._public_key, ec.EllipticCurvePublicKey)

    #
    # ---------------------------------
    # Type-specific (Ed25519, ECDSA secp256k1) to raw bytes or DER.
    # ---------------------------------
    #

    def to_bytes_raw(self) -> bytes:
        """
        Catch-all for convenience. 
        Serialize this PublicKey into its raw, algorithm-specific byte form.

        Ed25519 keys
        --------------
        - Always returns **32 bytes**.
        - These 32 bytes are the raw public-key point with no prefix or metadata.

        ECDSA (secp256k1) keys
        ------------------------
        - Returns the **compressed SEC1** form (33 bytes):
            1. A 1-byte prefix (0x02 or 0x03) indicating the parity of the Y coordinate  
            2. A 32-byte big-endian X coordinate  

        Returns:
            bytes:  
            - If `is_ed25519() == True`, a 32-byte Ed25519 point.  
            - Otherwise, a 33-byte compressed secp256k1 point.
        """
        if self.is_ed25519():
            return self.to_bytes_ed25519()
        # ECDSA
        return self.to_bytes_ecdsa()

    def to_bytes_ed25519(self) -> bytes:
        """
        Specific name for clarity.
        Returns the Ed25519 public key in 32-bytes raw form.
        """
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def to_bytes_ecdsa(self, compressed: bool = True) -> bytes:
        """
        Specific name for clarity.
        Returns the ECDSA public key in compressed or uncompressed form.
        """
        format_ = (serialization.PublicFormat.CompressedPoint
                if compressed
                else serialization.PublicFormat.UncompressedPoint)
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=format_
        )

    def to_bytes_der(self) -> bytes:
        """
        Returns the DER-encoded public key.
        """
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    #
    # ---------------------------------
    # Type-specific (Ed25519, ECDSA secp256k1) to hex string.
    # ---------------------------------
    #

    def to_string_ed25519(self) -> str:
        """
        Specific naming for clarity.
        Returns the Ed25519 public key as raw hex-encoded public key
        """
        return self.to_bytes_ed25519().hex()

    def to_string_ecdsa(self) -> str:
        """
        Specific naming for clarity.
        Returns the ECDSA public key as raw hex-encoded public key
        """
        return self.to_bytes_ecdsa().hex()

    def to_string_der(self) -> str:
        """
        Specific naming for clarity.
        Hex-encoded DER form of the public key.
        """
        return self.to_bytes_der().hex()

    def to_string_raw(self) -> str:
        """
        Catch all ed25519 or ecdsa for convenience.
        Returns the raw public key as a hex-encoded string.

        Example:
        >>> hex_str = pk.to_string_raw()
        >>> len(hex_str)
        64   # for Ed25519
        """
        return self.to_bytes_raw().hex()

    def to_string(self) -> str:
        """
        Returns the public key as a hex string (raw).
        Matches old usage that calls to_string().
        """
        return self.to_string_raw()

    #
    # ----------------------------
    # Signatures
    # ----------------------------
    #

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
        if self.is_ed25519():
            return self.verify_ed25519(signature, data)
        return self.verify_ecdsa(signature, data)

    def verify_ed25519(self, signature: bytes, data: bytes) -> None:
        """
        Verify an Ed25519 signature for clarity purposes. Raises InvalidSignature on failure.
        """
        if not isinstance(self._public_key, ed25519.Ed25519PublicKey):
            raise TypeError("Not an Ed25519 key")
        # Ed25519 has no external hash; the library does it internally.
        self._public_key.verify(signature, data)

    def verify_ecdsa(self, signature: bytes, data: bytes) -> None:
        """
        Verify an ECDSA (secp256k1) signature using SHA-256.

        Args:
            signature: DER-encoded signature bytes, or raw 64-byte signature (r + s concatenated, 32 bytes each)
            data:      The original message bytes.

        Raises:
            InvalidSignature: If the signature does not match.
        """
        if not isinstance(self._public_key, ec.EllipticCurvePublicKey):
            raise TypeError("Not an ECDSA key")
        
        # Convert raw 64-byte signature to DER format
        if len(signature) == 64:
            r = int.from_bytes(signature[:32], "big")
            s = int.from_bytes(signature[32:], "big")
            signature_der = asym_utils.encode_dss_signature(r, s)
        else:
            signature_der = signature
            
        data_hash = keccak256(data)
        self._public_key.verify(signature_der, data_hash, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256())))

    def __repr__(self) -> str:
        """
        Returns a string representation of the PublicKey.
        """
        if self.is_ed25519():
            return f"<PublicKey (Ed25519) hex={self.to_string_raw()}>"
        return f"<PublicKey (ECDSA) hex={self.to_string_raw()}>"
