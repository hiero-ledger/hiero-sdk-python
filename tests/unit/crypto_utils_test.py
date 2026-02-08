"""Unit tests for crypto_utils module."""

from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from hiero_sdk_python.utils.crypto_utils import (
    compress_point_unchecked,
    compress_with_cryptography,
    decompress_point,
    keccak256,
)

pytestmark = pytest.mark.unit


def test_keccak256():
    """Test keccak256 hashing."""
    # Known vector: empty string -> c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
    assert (
        keccak256(b"").hex()
        == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    )

    # "hello" -> 1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8
    assert (
        keccak256(b"hello").hex()
        == "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"
    )

    # "Transfer" -> 461a29a8a7db848c0827103038dd4776114eb182e0717208d0a793574936353d
    assert (
        keccak256(b"Transfer").hex()
        == "f099cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"
    )


def test_compress_point_unchecked():
    """Test point compression logic."""
    # Use cryptography to generate a valid point
    priv = ec.generate_private_key(ec.SECP256K1())
    pub = priv.public_key()
    nums = pub.public_numbers()
    x = nums.x
    y = nums.y

    compressed = compress_point_unchecked(x, y)
    assert len(compressed) == 33

    # Verify expected prefix
    expected_prefix = 0x03 if y % 2 else 0x02
    assert compressed[0] == expected_prefix
    assert int.from_bytes(compressed[1:], "big") == x


def test_decompress_point():
    """Test point decompression logic."""
    priv = ec.generate_private_key(ec.SECP256K1())
    pub = priv.public_key()
    nums = pub.public_numbers()

    # Create valid compressed point
    compressed = compress_point_unchecked(nums.x, nums.y)

    # Test decompression
    x, y = decompress_point(compressed)
    assert x == nums.x
    assert y == nums.y

    # Test uncompressed 65-byte format (0x04 + x + y)
    uncompressed = b"\x04" + nums.x.to_bytes(32, "big") + nums.y.to_bytes(32, "big")
    x2, y2 = decompress_point(uncompressed)
    assert x2 == nums.x
    assert y2 == nums.y

    # Test invalid length
    with pytest.raises(ValueError, match="Not recognized"):
        decompress_point(b"\x04" * 10)

    # Test invalid prefix
    with pytest.raises(ValueError, match="Not recognized"):
        # 0x05 is invalid prefix for 33-byte point
        invalid_point = b"\x05" + nums.x.to_bytes(32, "big")
        decompress_point(invalid_point)


def test_compress_with_cryptography():
    """Test compression using cryptography library."""
    priv = ec.generate_private_key(ec.SECP256K1())
    pub = priv.public_key()
    nums = pub.public_numbers()

    # Create uncompressed
    uncompressed = b"\x04" + nums.x.to_bytes(32, "big") + nums.y.to_bytes(32, "big")

    compressed_via_lib = compress_with_cryptography(uncompressed)
    compressed_manual = compress_point_unchecked(nums.x, nums.y)

    assert compressed_via_lib == compressed_manual
