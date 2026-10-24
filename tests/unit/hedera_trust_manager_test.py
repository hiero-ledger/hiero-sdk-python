"""Unit tests for _HederaTrustManager certificate validation."""

from __future__ import annotations

import hashlib

import pytest

from src.hiero_sdk_python.node import _HederaTrustManager


pytestmark = pytest.mark.unit


def test_trust_manager_init_with_cert_hash():
    """Test trust manager initialization with certificate hash."""
    cert_hash = b"abc123def456"
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=True)
    # UTF-8 decodable strings are decoded directly, not converted to hex
    assert trust_manager.cert_hash == cert_hash.decode("utf-8").lower()


def test_trust_manager_init_with_utf8_hex_string():
    """Test trust manager initialization with UTF-8 encoded hex string."""
    cert_hash = b"0xabc123def456"
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=True)
    assert trust_manager.cert_hash == "abc123def456"


def test_trust_manager_init_without_cert_hash_verification_disabled():
    """Test trust manager initialization without cert hash when verification disabled."""
    trust_manager = _HederaTrustManager(None, verify_certificate=False)
    assert trust_manager.cert_hash is None


def test_trust_manager_init_without_cert_hash_verification_enabled():
    """Test trust manager raises error when verification enabled but no cert hash."""
    with pytest.raises(ValueError, match="no applicable address book was found"):
        _HederaTrustManager(None, verify_certificate=True)


def test_trust_manager_init_with_empty_cert_hash_verification_enabled():
    """Test trust manager raises error when verification enabled but empty cert hash."""
    with pytest.raises(ValueError, match="no applicable address book was found"):
        _HederaTrustManager(b"", verify_certificate=True)


def test_trust_manager_check_server_trusted_matching_hash():
    """Test certificate validation with matching hash."""
    # Create a test PEM certificate
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----\n"
    cert_hash_bytes = hashlib.sha384(pem_cert).digest()
    cert_hash_hex = cert_hash_bytes.hex().lower()

    trust_manager = _HederaTrustManager(cert_hash_hex.encode("utf-8"), verify_certificate=True)
    # Should not raise
    assert trust_manager.check_server_trusted(pem_cert) is True


def test_trust_manager_check_server_trusted_mismatched_hash():
    """Test certificate validation raises error on hash mismatch."""
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----\n"
    wrong_hash = b"wrong_hash_value"

    trust_manager = _HederaTrustManager(wrong_hash, verify_certificate=True)

    with pytest.raises(ValueError, match="Failed to confirm the server's certificate"):
        trust_manager.check_server_trusted(pem_cert)


def test_trust_manager_check_server_trusted_no_verification():
    """Test certificate validation skipped when verification disabled."""
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----\n"

    trust_manager = _HederaTrustManager(None, verify_certificate=False)
    # Should not raise even without cert hash
    assert trust_manager.check_server_trusted(pem_cert) is True


def test_trust_manager_normalize_hash_with_0x_prefix():
    """Test hash normalization removes 0x prefix."""
    cert_hash = b"0xabc123"
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=True)
    assert trust_manager.cert_hash == "abc123"


def test_trust_manager_normalize_hash_lowercase():
    """Test hash normalization converts to lowercase."""
    cert_hash = b"ABC123DEF456"
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=True)
    assert trust_manager.cert_hash == "abc123def456"


def test_trust_manager_normalize_hash_unicode_decode_error():
    """Test hash normalization handles Unicode decode errors."""
    # Create bytes that can't be decoded as UTF-8
    cert_hash = bytes([0xFF, 0xFE, 0xFD])
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=True)
    # Should fall back to hex encoding
    assert trust_manager.cert_hash == cert_hash.hex().lower()


def test_trust_manager_init_with_raw_sha384_digest():
    """A raw 48-byte SHA-384 digest is normalized to its 96 character hex form."""
    raw_digest = hashlib.sha384(b"some certificate").digest()
    assert len(raw_digest) == 48

    trust_manager = _HederaTrustManager(raw_digest, verify_certificate=True)
    assert trust_manager.cert_hash == raw_digest.hex().lower()


@pytest.mark.parametrize("cert_hash", [b"", b"   ", b"0x", b"0X"])
def test_trust_manager_init_with_unusable_hash_fails_closed(cert_hash):
    """Whitespace/prefix-only hashes must not silently disable verification."""
    with pytest.raises(ValueError, match="no applicable address book was found"):
        _HederaTrustManager(cert_hash, verify_certificate=True)


@pytest.mark.parametrize("cert_hash", [b"", b"   ", b"0x", None])
def test_trust_manager_init_with_unusable_hash_and_verification_disabled(cert_hash):
    """Unusable hashes map to None when verification is explicitly disabled."""
    trust_manager = _HederaTrustManager(cert_hash, verify_certificate=False)
    assert trust_manager.cert_hash is None


def test_trust_manager_check_server_trusted_with_raw_sha384_digest():
    """A matching raw digest from the address book validates the certificate."""
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----\n"
    raw_digest = hashlib.sha384(pem_cert).digest()

    trust_manager = _HederaTrustManager(raw_digest, verify_certificate=True)
    assert trust_manager.check_server_trusted(pem_cert) is True


def test_trust_manager_check_server_trusted_non_ascii_hash_fails_closed():
    """A malformed (non-ASCII) expected hash fails closed instead of raising TypeError."""
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----\n"

    trust_manager = _HederaTrustManager(None, verify_certificate=False)
    trust_manager.cert_hash = "caf\u00e9"

    with pytest.raises(ValueError, match="Failed to confirm the server's certificate"):
        trust_manager.check_server_trusted(pem_cert)
