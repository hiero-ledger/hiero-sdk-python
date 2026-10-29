"""Signer callback type and helpers for building signature pairs."""

from __future__ import annotations

from collections.abc import Callable

from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2


Signer = Callable[[bytes], bytes]
"""
A signing callback: takes the canonical body bytes and returns the raw signature.

Ed25519 signers return the 64-byte signature. ECDSA (secp256k1) signers return the
64-byte ``r || s`` signature over the keccak256 hash of the bytes, as
``PrivateKey.sign`` does. This lets keys live outside the process, e.g. in an HSM or KMS.
"""


def _sign_to_signature_pair(
    public_key: PublicKey,
    signer: Signer,
    body_bytes: bytes,
) -> basic_types_pb2.SignaturePair:
    """
    Signs body_bytes with signer and wraps the result in a SignaturePair for public_key.

    Args:
        public_key (PublicKey): The public key matching the signer.
        signer (Signer): The signing callback.
        body_bytes (bytes): The bytes to sign.

    Returns:
        SignaturePair: The signature pair, keyed by the raw public key bytes.

    Raises:
        TypeError: If the signer does not return bytes.
    """
    signature = signer(body_bytes)

    if not isinstance(signature, bytes):
        raise TypeError(f"signer must return bytes, got {type(signature).__name__}")

    public_key_bytes = public_key.to_bytes_raw()

    if public_key.is_ed25519():
        return basic_types_pb2.SignaturePair(pubKeyPrefix=public_key_bytes, ed25519=signature)

    return basic_types_pb2.SignaturePair(pubKeyPrefix=public_key_bytes, ECDSA_secp256k1=signature)


def _signature_pair_to_key_and_signature(
    sig_pair: basic_types_pb2.SignaturePair,
) -> tuple[PublicKey, bytes]:
    """
    Unwraps a SignaturePair into its public key and raw signature.

    The key type is taken from the signature field, so 32-byte Ed25519 keys are never
    mistaken for anything else.

    Args:
        sig_pair (SignaturePair): The signature pair to unwrap.

    Returns:
        tuple[PublicKey, bytes]: The public key and the raw signature.

    Raises:
        ValueError: If the signature type is not Ed25519 or ECDSA (secp256k1), or if
            pubKeyPrefix is not a full public key (e.g. a shortened prefix).
    """
    signature_type = sig_pair.WhichOneof("signature")

    try:
        if signature_type == "ed25519":
            return PublicKey._from_bytes_ed25519(sig_pair.pubKeyPrefix), sig_pair.ed25519

        if signature_type == "ECDSA_secp256k1":
            return PublicKey.from_bytes_ecdsa(sig_pair.pubKeyPrefix), sig_pair.ECDSA_secp256k1
    except ValueError as e:
        raise ValueError(
            f"Cannot read the public key of a {signature_type} signature: pubKeyPrefix must be the full public key"
        ) from e

    raise ValueError(f"Unsupported signature type: {signature_type}")
