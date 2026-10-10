"""Unit tests for TLS functionality in _Node."""

from __future__ import annotations

import hashlib
import ssl
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.hiero_sdk_python.account.account_id import AccountId
from src.hiero_sdk_python.address_book.endpoint import Endpoint
from src.hiero_sdk_python.address_book.node_address import NodeAddress
from src.hiero_sdk_python.node import _Node, _normalize_cert_hash


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_address_book():
    """Create a mock address book with certificate hash."""
    cert_hash = b"test_cert_hash_12345"
    endpoint = Endpoint(address=b"node.example.com", port=50212, domain_name="node.example.com")
    return NodeAddress(account_id=AccountId(0, 0, 3), cert_hash=cert_hash, addresses=[endpoint])


@pytest.fixture
def mock_address_book_no_domain():
    """Create a mock address book without domain name."""
    cert_hash = b"test_cert_hash_12345"
    endpoint = Endpoint(address=b"127.0.0.1", port=50212, domain_name=None)
    return NodeAddress(account_id=AccountId(0, 0, 3), cert_hash=cert_hash, addresses=[endpoint])


@pytest.fixture
def mock_node_with_address_book(mock_address_book):
    """Create a node with address book."""
    return _Node(AccountId(0, 0, 3), "127.0.0.1:50212", mock_address_book)


@pytest.fixture
def mock_node_without_address_book():
    """Create a node without address book."""
    return _Node(AccountId(0, 0, 3), "127.0.0.1:50211", None)


def test_node_apply_transport_security_enable(mock_node_without_address_book):
    """Test enabling TLS on a node."""
    node = mock_node_without_address_book
    assert node._address._is_transport_security() is False

    node._apply_transport_security(True)
    assert node._address._is_transport_security() is True
    assert node._address._get_port() == 50212


def test_node_apply_transport_security_disable(mock_node_with_address_book):
    """Test disabling TLS on a node."""
    node = mock_node_with_address_book
    # Start with TLS enabled
    node._apply_transport_security(True)
    assert node._address._is_transport_security() is True

    node._apply_transport_security(False)
    assert node._address._is_transport_security() is False
    assert node._address._get_port() == 50211


def test_node_apply_transport_security_idempotent(mock_node_without_address_book):
    """Test that applying same TLS state is idempotent."""
    node = mock_node_without_address_book
    initial_port = node._address._get_port()

    node._apply_transport_security(False)  # Already disabled
    assert node._address._get_port() == initial_port


def test_node_apply_transport_security_closes_channel(mock_node_with_address_book):
    """Test that applying transport security closes existing channel."""
    node = mock_node_with_address_book
    # Disable verification to skip certificate fetching
    node._verify_certificates = False

    # Create a channel first
    with (
        patch("grpc.secure_channel") as mock_secure,
        patch.object(node, "_fetch_server_certificate_pem", return_value=b"dummy-cert"),
    ):
        mock_channel = Mock()
        mock_secure.return_value = mock_channel
        node._get_channel()
        assert node._channel is not None

        # Apply transport security change
        node._apply_transport_security(False)
        # Channel should be closed
        assert node._channel is None


def test_node_set_verify_certificates(mock_node_with_address_book):
    """Test setting certificate verification on node."""
    node = mock_node_with_address_book
    assert node._verify_certificates is True

    node._set_verify_certificates(False)
    assert node._verify_certificates is False


def test_node_set_verify_certificates_idempotent(mock_node_with_address_book):
    """Test that setting verification to same value is idempotent."""
    node = mock_node_with_address_book
    initial_state = node._verify_certificates

    node._set_verify_certificates(initial_state)
    node._set_verify_certificates(initial_state)

    assert node._verify_certificates == initial_state


def test_node_build_channel_options_with_hostname_not_override():
    """Test channel options include hostname override when domain differs from address."""
    endpoint = Endpoint(address=b"127.0.0.1", port=50212, domain_name="node.example.com")
    address_book = NodeAddress(account_id=AccountId(0, 0, 3), cert_hash=b"hash", addresses=[endpoint])
    node = _Node(AccountId(0, 0, 3), "127.0.0.1:50212", address_book)

    options = node._build_channel_options()
    assert options is not None
    assert ("grpc.ssl_target_name_override", "node.example.com") not in options


def test_node_build_channel_options_no_override_when_same():
    """Test channel options don't include override when hostname matches address."""
    endpoint = Endpoint(address=b"node.example.com", port=50212, domain_name="node.example.com")
    address_book = NodeAddress(account_id=AccountId(0, 0, 3), cert_hash=b"hash", addresses=[endpoint])
    node = _Node(AccountId(0, 0, 3), "node.example.com:50212", address_book)

    options = node._build_channel_options()
    assert options == [
        ("grpc.default_authority", "127.0.0.1"),
        ("grpc.ssl_target_name_override", "127.0.0.1"),
        ("grpc.keepalive_time_ms", 100000),
        ("grpc.keepalive_timeout_ms", 10000),
        ("grpc.keepalive_permit_without_calls", 1),
    ]


def test_node_build_channel_options_override_localhost_without_address_book(
    mock_node_without_address_book,
):
    """Test channel options don't include override without address book."""
    node = mock_node_without_address_book
    options = node._build_channel_options()
    assert options == [
        ("grpc.default_authority", "127.0.0.1"),
        ("grpc.ssl_target_name_override", "127.0.0.1"),
        ("grpc.keepalive_time_ms", 100000),
        ("grpc.keepalive_timeout_ms", 10000),
        ("grpc.keepalive_permit_without_calls", 1),
    ]


@patch("socket.create_connection")
@patch("ssl.create_default_context")
def test_node_fetch_server_certificate_pem(mock_ssl_context, mock_socket_conn, mock_node_with_address_book):
    """Test fetching server certificate in PEM format."""
    node = mock_node_with_address_book

    # Mock SSL context and socket
    mock_context = MagicMock()
    mock_ssl_context.return_value = mock_context
    mock_context.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = b"DER_CERT"

    mock_sock = MagicMock()
    mock_socket_conn.return_value.__enter__.return_value = mock_sock

    # Mock DER to PEM conversion
    with patch(
        "ssl.DER_cert_to_PEM_cert",
        return_value="-----BEGIN CERTIFICATE-----\nPEM\n-----END CERTIFICATE-----\n",
    ):
        pem_cert = node._fetch_server_certificate_pem()
        assert isinstance(pem_cert, bytes)
        assert b"BEGIN CERTIFICATE" in pem_cert


def test_node_validate_tls_certificate_with_trust_manager(mock_node_with_address_book):
    """Test certificate validation using trust manager."""
    node = mock_node_with_address_book
    node._verify_certificates = True

    # Mock certificate fetching
    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n"
    cert_hash = hashlib.sha384(pem_cert).digest().hex().lower()

    # Update address book with matching hash
    node._address_book._cert_hash = cert_hash.encode("utf-8")
    node._node_pem_cert = pem_cert

    with patch.object(node, "_fetch_server_certificate_pem", return_value=pem_cert):
        # Should not raise
        node._validate_tls_certificate_with_trust_manager()


def test_node_validate_tls_certificate_hash_mismatch(mock_node_with_address_book):
    """Test certificate validation raises error on hash mismatch."""
    node = mock_node_with_address_book
    node._verify_certificates = True

    pem_cert = b"-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n"
    wrong_hash = b"wrong_hash"
    node._address_book._cert_hash = wrong_hash
    node._node_pem_cert = pem_cert

    with pytest.raises(ValueError, match="Failed to confirm the server's certificate"):
        node._validate_tls_certificate_with_trust_manager()


def test_node_validate_tls_certificate_no_verification(mock_node_with_address_book):
    """Test certificate validation skipped when verification disabled."""
    node = mock_node_with_address_book
    node._verify_certificates = False

    # Should not raise even without proper setup
    node._validate_tls_certificate_with_trust_manager()


def test_node_validate_tls_certificate_no_address_book():
    """Test certificate validation fails closed when no address book exists."""
    node = _Node(AccountId(0, 0, 3), "127.0.0.1:50212", None)
    node._verify_certificates = True
    node._address = node._address._to_secure()

    # Validation must NOT be skipped: without a trust anchor (address book hash
    # or configured root certificates) verification cannot be performed, so
    # fail closed to prevent an intercepted cert becoming its own trust anchor.
    with pytest.raises(ValueError, match="no applicable address book was found"):
        node._validate_tls_certificate_with_trust_manager()


@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_node_get_channel_secure(mock_insecure, mock_secure, mock_node_with_address_book):
    """Test channel creation for secure connection."""
    node = mock_node_with_address_book
    node._address = node._address._to_secure()  # Ensure TLS is enabled

    with patch.object(node, "_fetch_server_certificate_pem", return_value=b"dummy-cert"):
        mock_channel = Mock()
        mock_secure.return_value = mock_channel

        # Skip certificate validation for this test
        node._verify_certificates = False

        channel = node._get_channel()

        mock_secure.assert_called_once()
        mock_insecure.assert_not_called()
        assert channel is not None


@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_node_get_channel_insecure(mock_insecure, mock_secure, mock_node_without_address_book):
    """Test channel creation for insecure connection."""
    node = mock_node_without_address_book

    mock_channel = Mock()
    mock_insecure.return_value = mock_channel

    channel = node._get_channel()

    mock_insecure.assert_called_once()
    mock_secure.assert_not_called()
    assert channel is not None


@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_node_get_channel_reuses_existing(mock_insecure, mock_secure, mock_node_with_address_book):  # noqa: ARG001
    """Test that channel is reused when already created."""
    node = mock_node_with_address_book
    node._verify_certificates = False

    with patch.object(node, "_fetch_server_certificate_pem", return_value=b"dummy-cert"):
        mock_channel = Mock()
        mock_secure.return_value = mock_channel

        channel1 = node._get_channel()
        channel2 = node._get_channel()

        # Should only create channel once
        assert mock_secure.call_count == 1
        assert channel1 is channel2


def test_node_set_root_certificates(mock_node_with_address_book):
    """Test setting root certificates on node."""
    node = mock_node_with_address_book
    custom_certs = b"custom_root_certs"

    node._set_root_certificates(custom_certs)
    assert node._root_certificates == custom_certs


def test_node_set_root_certificates_closes_channel(mock_node_with_address_book):
    """Test that setting root certificates closes existing channel."""
    node = mock_node_with_address_book
    node._verify_certificates = False

    with (
        patch("grpc.secure_channel") as mock_secure,
        patch.object(node, "_fetch_server_certificate_pem", return_value=b"dummy-cert"),
    ):
        mock_channel = Mock()
        mock_secure.return_value = mock_channel
        node._get_channel()
        assert node._channel is not None

        node._set_root_certificates(b"certs")
        # Channel should be closed to force recreation
        assert node._channel is None


@patch("socket.create_connection", side_effect=ConnectionRefusedError)
@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_secure_connect_raise_error_if_no_certificate_is_available(
    mock_insecure,
    mock_secure,
    mock_conn,
    mock_node_without_address_book,
):
    """Test get channel fails closed before even fetching when no trust anchor exists."""
    node = mock_node_without_address_book
    node._apply_transport_security(True)

    with pytest.raises(ValueError, match="no applicable address book was found"):
        node._get_channel()

    # The fetch must never be attempted and no channel of any kind created.
    mock_conn.assert_not_called()
    mock_secure.assert_not_called()
    mock_insecure.assert_not_called()


@patch("socket.create_connection", side_effect=ConnectionRefusedError)
@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_secure_connect_raises_when_no_certificate_even_with_verification_disabled(
    mock_insecure,
    mock_secure,
    mock_conn,
    mock_node_without_address_book,
):
    """No certificate fails closed, even if certificate verification is disabled."""
    node = mock_node_without_address_book
    node._apply_transport_security(True)
    node._set_verify_certificates(False)

    with pytest.raises(ValueError, match="No certificate available."):
        node._get_channel()

    mock_secure.assert_not_called()
    mock_insecure.assert_not_called()


@patch("grpc.secure_channel")
@patch("grpc.insecure_channel")
def test_node_get_channel_successful_fetch_without_address_book_fails_closed(
    mock_insecure,
    mock_secure,
    mock_node_without_address_book,
):
    """
    A fetched certificate without a trust anchor must not be used as its own
    root certificate.

    Even when the certificate fetch succeeds, a node without an address book
    (e.g. a fallback node) cannot validate the fetched certificate, so channel
    creation must fail closed before grpc.secure_channel is ever called.
    """
    node = mock_node_without_address_book
    node._address = node._address._to_secure()

    # Certificate fetch SUCCEEDS (mimics an on-path attacker answering the
    # unauthenticated TLS handshake with a certificate of their choice).
    with (
        patch.object(node, "_fetch_server_certificate_pem", return_value=b"attacker-cert"),
        pytest.raises(ValueError, match="no applicable address book was found"),
    ):
        node._get_channel()

    # No channel of any kind was created: the intercepted certificate is never
    # installed as a trust root.
    mock_secure.assert_not_called()
    mock_insecure.assert_not_called()


@patch("grpc.secure_channel")
def test_node_get_channel_successful_fetch_without_address_book_but_root_certificates(
    mock_secure,
    mock_node_without_address_book,
):
    """
    Explicitly configured root certificates remain a valid trust anchor even
    without an address book, so the secure channel is still created.
    """
    node = mock_node_without_address_book
    node._address = node._address._to_secure()
    node._set_root_certificates(b"explicit-root-certs")

    with patch.object(node, "_fetch_server_certificate_pem") as mock_fetch:
        mock_channel = Mock()
        mock_secure.return_value = mock_channel

        channel = node._get_channel()

        # The fetched certificate is not needed: the configured roots are the
        # trust anchor and the TLS stack validates against them.
        mock_fetch.assert_not_called()
        assert node._node_pem_cert == b"explicit-root-certs"
        assert channel is not None


@patch("grpc.secure_channel")
def test_node_get_channel_with_root_certificates(mock_secure, mock_node_with_address_book):
    """Test secure channel uses provided root certificates."""
    node = mock_node_with_address_book
    node._address = node._address._to_secure()

    # Skip certificate verification (consistent with other tests)
    node._verify_certificates = False

    root_certs = b"custom_root_certificates"
    node._set_root_certificates(root_certs)

    with patch.object(node, "_fetch_server_certificate_pem") as mock_fetch:
        mock_channel = Mock()
        mock_secure.return_value = mock_channel

        channel = node._get_channel()

        # Root certificates should be used directly
        assert node._node_pem_cert == root_certs

        # Server certificate should not be fetched
        mock_fetch.assert_not_called()
        assert channel is not None


@pytest.mark.parametrize(
    "cert_hash, expected",
    [
        (b"TestCertHashABC", "testcerthashabc"),
        # Remove 0x prefix
        (b"0xABCDEF1234", "abcdef1234"),
        (b"  AbCdEf  ", "abcdef"),
        (b"abcdef123456", "abcdef123456"),
        (b"\xff\xfe\xfd\xfc", "fffefdfc"),
        # A raw 48-byte SHA-384 digest (as carried by the protobuf address book)
        # is hex encoded; it cannot be mistaken for text here because it contains
        # bytes that are not ASCII hex digits.
        (bytes(range(48)), bytes(range(48)).hex()),
        (b"\x00" * 48, (b"\x00" * 48).hex()),
        # Hex text wins for exactly 48 characters, even though 48 bytes is also
        # the raw SHA-384 digest length.
        (b"a" * 48, "a" * 48),
        (b"AB" * 24, "ab" * 24),
        (b"0x" + b"ab" * 23, "ab" * 23),
        (b"0X" + b"ab" * 23, "ab" * 23),
        (b"deadbeef" * 6, "deadbeef" * 6),
        # Whitespace disqualifies the hex-text reading of a 48-byte value,
        # so it falls back to treating it as a raw digest.
        (b" " + b"a" * 47, (b" " + b"a" * 47).hex()),
        (b" " * 48, (b" " * 48).hex()),
        # No usable fingerprint
        (None, None),
        (b"", None),
        (b"   ", None),
        (b"0x", None),
        # Bytes-like values other than ``bytes`` are handled too
        (bytearray(b"0xABCDEF1234"), "abcdef1234"),
        (bytearray(bytes(range(48))), bytes(range(48)).hex()),
    ],
)
def test_normalize_cert_hash(cert_hash, expected):
    """Test certificate hash normalization."""
    result = _normalize_cert_hash(cert_hash)
    assert result == expected


@pytest.mark.parametrize("cert_hash", ["0x1234abcd", 12345, ["0x12"]])
def test_normalize_cert_hash_rejects_non_bytes(cert_hash):
    """Non bytes-like values fail closed instead of raising a TypeError."""
    assert _normalize_cert_hash(cert_hash) is None


def test_normalize_cert_hash_prefers_hex_text_for_48_ascii_hex_characters():
    """
    A 48 character ASCII hex string is text, not the hex encoding of its bytes.

    Regression test: treating every 48-byte value as a raw digest turned such a
    fingerprint into a wrong 96 character value that could never match.
    """
    supplied = b"deadbeef" * 6  # exactly 48 ASCII hex characters
    assert len(supplied) == 48

    assert _normalize_cert_hash(supplied) == supplied.decode("ascii")
    assert _normalize_cert_hash(supplied) != supplied.hex()


def test_validate_tls_skipped_when_not_secure(mock_node_with_address_book):
    """Test skip validate_certificate when insrcure connection is use"""
    node = mock_node_with_address_book
    # Force insecure transport
    node._address = node._address._to_insecure()
    node._verify_certificates = True

    # Should return early and NOT raise
    node._validate_tls_certificate_with_trust_manager()


@patch("socket.create_connection")
@patch("ssl.create_default_context")
def test_fetch_server_certificate_legacy_tls_path(mock_ssl_context, mock_socket):
    """Test ssl_context with enforce TLS verison restiction."""
    node = _Node(AccountId(0, 0, 3), "127.0.0.1:50212", Mock())

    mock_context = MagicMock()
    # Simulate Python < 3.7
    delattr(mock_context, "minimum_version")
    mock_context.options = 0

    mock_ssl_context.return_value = mock_context

    mock_tls_socket = MagicMock()
    mock_tls_socket.getpeercert.return_value = b"DER_CERT"

    mock_context.wrap_socket.return_value.__enter__.return_value = mock_tls_socket
    mock_socket.return_value.__enter__.return_value = MagicMock()

    with patch("ssl.DER_cert_to_PEM_cert", return_value="PEM"):
        node._fetch_server_certificate_pem()

    # Assert legacy flags applied
    assert mock_context.options & ssl.OP_NO_TLSv1
    assert mock_context.options & ssl.OP_NO_TLSv1_1
