import hashlib
import math
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

try:
    from Crypto.Hash import keccak
except ImportError:
    keccak = None


SECP256K1_CURVE = ec.SECP256K1()


def keccak256(data: bytes) -> bytes:
    """
    Mirroring the Java code's `Crypto.calcKeccak256`.
    """
    global keccak
    if keccak is None:
        raise RuntimeError("Keccak not available. Install pycryptodome or similar.")
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()


def compress_point_unchecked(x: int, y: int) -> bytes:
    """
    Compress an (x, y) for secp256k1 (or similar). 33 bytes: [0x02 or 0x03] + x(32).
    sign bit of y => 0x03 if odd, 0x02 if even
    """
    prefix = 0x02 | (y & 1) 
    return bytes([prefix]) + x.to_bytes(32, "big")


def decompress_point(data: bytes) -> Tuple[int, int]:
    """
    Decompress a 33-byte point for secp256k1 into (x, y).
    If 65 bytes, interpret as uncompressed and re-compress or decode, etc.
    """
    if len(data) == 65 and data[0] == 0x04:
        x = int.from_bytes(data[1:33], "big")
        y = int.from_bytes(data[33:], "big")
        return (x, y)
    elif len(data) == 33 and (data[0] in (0x02, 0x03)):
        x = int.from_bytes(data[1:], "big")
    else:
        raise ValueError("Not recognized as compressed or uncompressed SEC1 point.")

    point = ec.EllipticCurvePublicKey.from_encoded_point(SECP256K1_CURVE, data).public_numbers()
    return (point.x, point.y)


def compress_with_cryptography(encoded: bytes) -> bytes:
    """
    Takes either a 33-byte compressed or 65-byte uncompressed,
    returns a 33-byte compressed via cryptography.
    """
    pub = ec.EllipticCurvePublicKey.from_encoded_point(SECP256K1_CURVE, encoded)
    compressed = pub.public_bytes(
        ec.Encoding.X962, ec.PublicFormat.CompressedPoint
    )
    return compressed
