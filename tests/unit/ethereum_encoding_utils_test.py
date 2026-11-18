from __future__ import annotations

import pytest

from hiero_sdk_python.utils.ethereum_encoding_utils import (
    _UINT64_MAX,
    _big_int_to_eth_bytes,
    _eth_bytes_to_big_int,
    _eth_bytes_to_uint64,
    _uint64_to_eth_bytes,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("value", "encoded_hex"), [(0, ""), (1, "01"), (10, "0a"), (256, "0100"), (0xFFF, "0fff"), (0xDEADBEEF, "deadbeef")]
)
def test_uint64_encoding(value, encoded_hex):
    """Test uint64 encoding."""
    encoded_bytes = _uint64_to_eth_bytes(value)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == encoded_hex


@pytest.mark.parametrize("value", [_UINT64_MAX + 1, -1])
def test_uint64_encoding_rejects_out_of_range_values(value):
    """Test that uint64 encoding rejects values outside the valid range."""
    with pytest.raises(ValueError, match="value is out of range for uint64"):
        _uint64_to_eth_bytes(value)


@pytest.mark.parametrize("value", ["1", b"1", True, 0.1, None, {}, []])
def test_uint64_encoding_rejects_invalid_type(value):
    """Test that uint64 encoding rejects invalid type."""
    with pytest.raises(TypeError, match="value must be of type int"):
        _uint64_to_eth_bytes(value)


@pytest.mark.parametrize("value", [b"", None])
def test_eth_bytes_to_uint64_handle_none_and_empty(value):
    """Test bytes to uint64 decoding handles empty and None bytes."""
    decoded_value = _eth_bytes_to_uint64(value)
    assert decoded_value == 0


def test_eth_bytes_to_uint64_handles_long_bytes():
    """Test _eth_bytes_to_uint64 handle longer than 8 bytes byt retaining only the least significant 8 bytes."""
    value = bytes.fromhex("01000000000000000a")  # b'\x01\x00\x00\x00\x00\x00\x00\x00\n' (9 bytes)
    decoded_value = _eth_bytes_to_uint64(value)  # truncate to lower 8 bytes i.e b'\x00\x00\x00\x00\x00\x00\x00\n'
    assert decoded_value == 10


@pytest.mark.parametrize("value", ["1", 1, True, 0.1, {}, []])
def test_eth_bytes_to_uint64_rejects_invalid_type(value):
    """Test that bytes to uint64 decoding rejects invalid type."""
    with pytest.raises(TypeError, match="parameter must be of type bytes"):
        _eth_bytes_to_uint64(value)


@pytest.mark.parametrize("value", [0, 1, 10, 256, 0xFFF, 0xDEADBEEF, _UINT64_MAX])
def test_uint64_encoding_roundtrip(value):
    """Test uint64 encoding roundtrip."""
    encoded_bytes = _uint64_to_eth_bytes(value)
    decoded_value = _eth_bytes_to_uint64(encoded_bytes)

    assert decoded_value == value


@pytest.mark.parametrize(
    ("value", "encoded_hex"), [(0, ""), (1, "01"), (10, "0a"), (128, "80"), (1000000000000000000, "0de0b6b3a7640000")]
)
def test_big_int_encoding(value, encoded_hex):
    """Test big int encoding."""
    encoded_bytes = _big_int_to_eth_bytes(value)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == encoded_hex


def test_big_int_encoding_handle_none():
    """Test big int encoding handles none."""
    encoded_bytes = _big_int_to_eth_bytes(None)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == ""


@pytest.mark.parametrize(("value", "encoded_hex"), [(-1, "01"), (-10, "0a")])
def test_big_int_encoding_with_negatives(value, encoded_hex):
    """Test big int encoding for negative values."""
    encoded_bytes = _big_int_to_eth_bytes(value)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == encoded_hex


@pytest.mark.parametrize(
    ("value", "encoded_hex"),
    [(10**30, "0c9f2c9cd04674edea40000000"), (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, "ffffffffffffffffffffffffffffffff")],
)
def test_big_int_encoding_handle_large_value(value, encoded_hex):
    """Test big int encoding handle larger values."""
    encoded_bytes = _big_int_to_eth_bytes(value)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == encoded_hex


@pytest.mark.parametrize("value", ["1", b"1", True, 0.1, {}, []])
def test_big_int_encoding_rejects_invalid_type(value):
    """Test that big int encoding rejects invalid type."""
    with pytest.raises(TypeError, match="value must be of type int"):
        _big_int_to_eth_bytes(value)


@pytest.mark.parametrize("value", [b"", None])
def test_eth_bytes_to_big_int_handle_none_and_empty(value):
    """Test bytes to big int decoding handles empty and None bytes."""
    decoded_value = _eth_bytes_to_big_int(value)
    assert decoded_value == 0


@pytest.mark.parametrize("value", ["1", 1, True, 0.1, {}, []])
def test_eth_bytes_to_big_int_rejects_invalid_type(value):
    """Test that bytes to big int decoding rejects invalid type."""
    with pytest.raises(TypeError, match="parameter must be of type bytes"):
        _eth_bytes_to_big_int(value)


@pytest.mark.parametrize("value", [0, 1, 10, 128, 0xDEADBEEF, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1000000000000000000])
def test_big_int_roundtrip(value):
    """Test big int encoding roundtrip."""
    encoded_bytes = _big_int_to_eth_bytes(value)
    decoded_value = _eth_bytes_to_big_int(encoded_bytes)

    assert decoded_value == value
