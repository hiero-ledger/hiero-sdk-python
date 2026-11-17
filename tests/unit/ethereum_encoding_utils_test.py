from __future__ import annotations

import pytest

from hiero_sdk_python.utils.ethereum_encoding_utils import _UINT64_MAX, _eth_bytes_to_uint64, _uint64_to_eth_bytes


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(("value", "encoded_hex"), [(0, ""), (1, "01"), (256, "0100"), (0xDEADBEEF, "deadbeef")])
def test_uint64_encoding(value, encoded_hex):
    """Test uint64 encoding."""
    encoded_bytes = _uint64_to_eth_bytes(value)
    assert encoded_bytes is not None
    assert encoded_bytes.hex() == encoded_hex


@pytest.mark.parametrize("value", [_UINT64_MAX + 1, -1])
def test_uint64_encoding_rejects_out_of_range_values(value):
    """Test that uint64 encoding rejects values outside the valid range."""
    with pytest.raises(ValueError, match=f"value {value} is out of range for uint64"):
        _uint64_to_eth_bytes(value)


@pytest.mark.parametrize("value", ["1", b"1", True, 0.1, None, {}, []])
def test_uint64_encoding_rejects_invalid_type(value):
    """Test that uint64 encoding rejects invalid type."""
    with pytest.raises(TypeError, match="value must be of type int"):
        _uint64_to_eth_bytes(value)


def test_eth_bytes_to_uint64_retrun_0_for_none():
    """Test bytes to uint64 decoding return 0 for bytes as None."""
    decoded_value = _eth_bytes_to_uint64(None)
    assert decoded_value == 0


@pytest.mark.parametrize("value", ["1", 1, True, 0.1, {}, []])
def test_eth_bytes_to_uint64_rejects_invalid_type(value):
    """Test that bytes to uint64 decoding rejects invalid type."""
    with pytest.raises(TypeError, match="parameter must be of type bytes"):
        _eth_bytes_to_uint64(value)


@pytest.mark.parametrize("value", [0, 1, 256, 0xDEADBEEF, _UINT64_MAX])
def test_uint64_encoding_roundtrip(value):
    """Test uint64 encoding roundtrip."""
    encoded_bytes = _uint64_to_eth_bytes(value)
    decoded_value = _eth_bytes_to_uint64(encoded_bytes)

    assert decoded_value == value
