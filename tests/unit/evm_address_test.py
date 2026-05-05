from __future__ import annotations

import re

import pytest

from hiero_sdk_python.crypto.evm_address import EvmAddress


pytestmark = pytest.mark.unit


def test_is_valid_accepts_valid_address():
    """Test validation accepts a valid EVM address."""
    assert EvmAddress.is_valid("0x52908400098527886E0F7030069857D2E4169EE7")


def test_is_valid_rejects_non_string():
    """Test validation rejects non-string inputs."""
    assert not EvmAddress.is_valid(123)


def test_is_checksum_valid_rejects_missing_prefix():
    """Test checksum validation rejects addresses without ``0x`` prefix."""
    assert not EvmAddress.is_checksum_valid("52908400098527886E0F7030069857D2E4169EE7")


def test_is_checksum_valid_rejects_invalid_length():
    """Test checksum validation rejects addresses with invalid length."""
    assert not EvmAddress.is_checksum_valid("0x123")


def test_is_checksum_valid_rejects_non_hex():
    """Test checksum validation rejects non-hexadecimal addresses."""
    assert not EvmAddress.is_checksum_valid("0xZZZZ8400098527886E0F7030069857D2E4169EE7")


def test_is_valid_accepts_lowercase_without_prefix():
    """Test validation accepts lowercase addresses without ``0x``."""
    assert EvmAddress.is_valid("52908400098527886e0f7030069857d2e4169ee7")


def test_is_valid_rejects_invalid_length():
    """Test validation rejects addresses with invalid length."""
    assert not EvmAddress.is_valid("123")


def test_is_checksum_valid_rejects_non_string():
    """Test checksum validation rejects non-string inputs."""
    assert not EvmAddress.is_checksum_valid(123)


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


def test_to_checksum_address_matches_eip55_reference():
    """Test checksum formatting follows EIP-55."""
    addr = EvmAddress.from_string("0x52908400098527886e0f7030069857d2e4169ee7")

    assert addr.to_checksum_address() == "0x52908400098527886E0F7030069857D2E4169EE7"


def test_to_checksum_address_is_stable_for_lowercase_input():
    """Test checksum formatting works for all-lower input."""
    addr = EvmAddress.from_string("de709f2102306220921060314715629080e2fb77")

    assert addr.to_checksum_address() == "0xde709f2102306220921060314715629080e2fb77"


def test_checksum_from_mixed_case():
    """Test checksum generation normalizes mixed-case input."""
    addr = EvmAddress.from_string("52908400098527886E0f7030069857d2e4169ee7")

    assert addr.to_checksum_address() == "0x52908400098527886E0F7030069857D2E4169EE7"


def test_is_checksum_valid():
    """Test checksum validation accepts valid EIP-55 addresses."""
    assert EvmAddress.is_checksum_valid("0x52908400098527886E0F7030069857D2E4169EE7")


def test_invalid_checksum():
    """Test checksum validation rejects incorrectly cased addresses."""
    assert not EvmAddress.is_checksum_valid("0x52908400098527886e0f7030069857d2e4169ee7")


def test_invalid_embedded_prefix():
    """Test embedded ``0x`` substrings are rejected as invalid addresses."""
    bad = "52908400098527886e0f70300698" + "0x" + "57d2e4169ee7"

    assert not EvmAddress.is_valid(bad)

    with pytest.raises(ValueError):
        EvmAddress.normalize(bad)


def test_normalize():
    """Test normalization returns lowercase address without ``0x`` prefix."""
    assert (
        EvmAddress.normalize("0x52908400098527886E0F7030069857D2E4169EE7") == "52908400098527886e0f7030069857d2e4169ee7"
    )
