from __future__ import annotations

import re

import pytest

from hiero_sdk_python.crypto.evm_address import EvmAddress


pytestmark = pytest.mark.unit


def test_from_string_without_prefix():
    """Test creating EvmAddress from valid 40-character hex string."""
    hex_str = "1234567890abcdef1234567890abcdef12345678"
    addr = EvmAddress.from_string(hex_str)

    assert isinstance(addr, EvmAddress)
    assert addr.to_string() == hex_str
    assert len(addr.address_bytes) == 20


def test_from_string_with_0x_prefix():
    """Test creating EvmAddress from valid hex string with '0x' prefix."""
    hex_str = "0x1234567890abcdef1234567890abcdef12345678"
    addr = EvmAddress.from_string(hex_str)

    assert isinstance(addr, EvmAddress)
    assert addr.to_string() == hex_str[2:]
    assert len(addr.address_bytes) == 20


def test_from_string_invalid_length():
    """Test ValueError for invalid hex string length."""
    with pytest.raises(ValueError):
        EvmAddress.from_string("0x1234")


def test_from_string_invalid_hex_characters():
    """Test ValueError for invalid hex characters."""
    with pytest.raises(ValueError):
        EvmAddress.from_string("0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")


def test_from_string_with_surrounding_whitespace():
    """Surrounding whitespace (from .env, JSON config, shell vars) should be stripped, not rejected."""
    hex_no_prefix = "1234567890abcdef1234567890abcdef12345678"
    hex_with_prefix = "0x1234567890abcdef1234567890abcdef12345678"

    assert EvmAddress.from_string(f"  {hex_no_prefix}  ").to_string() == hex_no_prefix
    assert EvmAddress.from_string(f"\n{hex_with_prefix}\n").to_string() == hex_no_prefix
    assert EvmAddress.from_string(f"\t{hex_with_prefix}\t").to_string() == hex_no_prefix


def test_from_bytes_valid():
    """Test creating EvmAddress from 20 bytes."""
    raw = bytes(range(20))
    addr = EvmAddress.from_bytes(raw)

    assert isinstance(addr, EvmAddress)
    assert addr.address_bytes == raw
    assert addr.to_string() == raw.hex()


def test_from_bytes_invalid_length():
    """Test ValueError for byte length not equal to 20."""
    with pytest.raises(ValueError):
        EvmAddress.from_bytes(bytes(range(10)))


def test_equality():
    """Test equality and hash behavior."""
    raw = bytes(range(20))
    addr1 = EvmAddress.from_bytes(raw)
    addr2 = EvmAddress.from_string("0x" + raw.hex())

    assert addr1 == addr2


def test_to_proto_key():
    """Test to_proto_key raises error when call."""
    raw = bytes(range(20))
    address = EvmAddress.from_bytes(raw)

    with pytest.raises(RuntimeError, match=re.escape("to_proto_key() not implemented for EvmAddress")):
        address.to_proto_key()
