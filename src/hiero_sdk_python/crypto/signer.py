"""Signer callback type and helpers for building signature pairs."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from hiero_sdk_python.hapi.services import basic_types_pb2


if TYPE_CHECKING:
    from hiero_sdk_python.crypto.public_key import PublicKey


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
