from __future__ import annotations

import hashlib
import hmac
import logging
import socket
import ssl  # Python's ssl module implements TLS (despite the name)
import time

import grpc

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.channels import _Channel, _UserAgentInterceptor
from hiero_sdk_python.managed_node_address import _ManagedNodeAddress


# Timeout for fetching server certificates during TLS validation
CERT_FETCH_TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)

# Length of a raw SHA-384 digest (the form carried by the protobuf address book).
_SHA384_DIGEST_LENGTH = hashlib.sha384().digest_size

# Lowercase ASCII hexadecimal digits, used to tell hex text apart from a raw digest.
_HEX_DIGITS = frozenset("0123456789abcdef")


def _is_hex_text(value: bytes | bytearray) -> bool:
    """
    Whether ``value`` reads as (optionally ``0x`` prefixed) ASCII hexadecimal text.

    An empty string, or one that is only the ``0x`` prefix, is not text.
    """
    try:
        text = bytes(value).decode("ascii")
    except UnicodeDecodeError:
        return False

    digits = text[2:] if text[:2].lower() == "0x" else text
    return len(digits) > 0 and all(character in _HEX_DIGITS for character in digits.lower())


def _normalize_cert_hash(cert_hash: bytes | None) -> str | None:
    """
    Normalize a certificate hash to a lowercase hexadecimal string.

    Args:
        cert_hash: Raw digest bytes, or UTF-8 (optionally ``0x`` prefixed) hex text.

    Returns:
        str | None: Lowercase hex fingerprint, or None when no usable hash is
        present (not bytes-like, empty, whitespace only, or ``0x`` only).
    """
    if not isinstance(cert_hash, (bytes, bytearray)) or len(cert_hash) == 0:
        return None

    if len(cert_hash) == _SHA384_DIGEST_LENGTH and not _is_hex_text(cert_hash):
        return bytes(cert_hash).hex().lower()

    try:
        decoded = cert_hash.decode("utf-8").strip().lower()
    except UnicodeDecodeError:
        return bytes(cert_hash).hex().lower() or None

    if decoded.startswith("0x"):
        decoded = decoded[2:]

    return decoded or None


_NO_TRUST_ANCHOR_MESSAGE = (
    "Transport security and certificate verification are enabled, but no applicable address book was found"
)


class _HederaTrustManager:
    """
    Python equivalent of Java's HederaTrustManager.
    Validates server certificates by comparing SHA-384 hashes of PEM-encoded certificates
    against expected hashes from the address book.
    """

    def __init__(self, cert_hash: bytes | None, verify_certificate: bool):
        """
        Initialize the trust manager.

        Args:
            cert_hash: Expected certificate hash from the address book. Either the
                raw SHA-384 digest (48 bytes) or its UTF-8 encoded hexadecimal
                representation (optionally prefixed with ``0x``).
            verify_certificate: Whether to enforce certificate verification
        """
        normalized_hash = _normalize_cert_hash(cert_hash)

        self.verify_certificate: bool = verify_certificate
        self.cert_hash: str | None = normalized_hash

        if self.cert_hash is None and verify_certificate:
            raise ValueError(_NO_TRUST_ANCHOR_MESSAGE)

    def check_server_trusted(self, pem_cert: bytes) -> bool:
        """
        Validate a server certificate by comparing its hash to the expected hash.

        Args:
            pem_cert: PEM-encoded certificate bytes

        Returns:
            True if certificate hash matches expected hash

        Raises:
            ValueError: If certificate hash doesn't match expected hash
        """
        if self.cert_hash is None:
            return True

        # Compute SHA-384 hash of PEM certificate (matching Java implementation)
        actual_hash = hashlib.sha384(pem_cert).hexdigest()

        try:
            hash_matches = hmac.compare_digest(actual_hash, self.cert_hash)
        except TypeError:
            hash_matches = False

        if not hash_matches:
            raise ValueError(
                f"Failed to confirm the server's certificate from a known address book. "
                f"Expected hash: {self.cert_hash}, received hash: {actual_hash}"
            )

        return True


class _Node:
    def __init__(
        self,
        account_id: AccountId,
        address: str,
        address_book: NodeAddress | None = None,
    ):
        """
        Initialize a new Node instance.

        Args:
            account_id (AccountId): The account ID of the node.
            address (str): The address of the node.
            address_book (NodeAddress | None): The address-book entry for the node.
                ``None`` when the node was built without address-book metadata.
        """
        self._account_id: AccountId = account_id
        self._channel: _Channel | None = None
        self._address_book: NodeAddress | None = address_book
        self._address: _ManagedNodeAddress = _ManagedNodeAddress._from_string(address)
        self._verify_certificates: bool = True
        self._root_certificates: bytes | None = None
        self._node_pem_cert: bytes | None = None

        self._min_backoff: float = 8  # seconds
        self._max_backoff: float = 3600  # seconds
        self._current_backoff: float = self._min_backoff
        self._readmit_time: float = time.monotonic()
        self._bad_grpc_response_count: int = 0

    def _close(self):
        """
        Close the channel for this node.

        Returns:
            None
        """
        if self._channel is not None:
            self._channel.channel.close()
            self._channel = None

    def _get_channel(self):
        """
        Get the channel for this node.

        Returns:
            _Channel: The channel for this node.
        """
        if self._channel:
            return self._channel

        if self._address._is_transport_security():
            if self._verify_certificates and not self._has_trust_anchor():
                raise ValueError(_NO_TRUST_ANCHOR_MESSAGE)

            if self._root_certificates:
                # Use the certificate that is provided
                self._node_pem_cert = self._root_certificates

            else:
                # Fetch pem_cert for the node (a trust anchor was verified above).
                # Returns None if the handshake fails(unreachable host, no TLS listener)
                self._node_pem_cert = self._fetch_server_certificate_pem()

            if not self._node_pem_cert:
                raise ValueError("No certificate available.")

            # Validate certificate if verification is enabled
            if self._verify_certificates:
                self._validate_tls_certificate_with_trust_manager()

            options = self._build_channel_options()
            credentials = grpc.ssl_channel_credentials(
                root_certificates=self._node_pem_cert,
                private_key=None,
                certificate_chain=None,
            )
            channel = grpc.secure_channel(str(self._address), credentials, options=options)
        else:
            channel = grpc.insecure_channel(str(self._address))

        channel = grpc.intercept_channel(channel, _UserAgentInterceptor())

        self._channel = _Channel(channel)

        return self._channel

    def _apply_transport_security(self, enabled: bool):
        """Update the node's address to use secure or insecure transport."""
        if enabled and self._address._is_transport_security():
            return
        if not enabled and not self._address._is_transport_security():
            return

        self._close()

        if enabled:
            self._address = self._address._to_secure()
        else:
            self._address = self._address._to_insecure()

    def _set_root_certificates(self, root_certificates: bytes | None):
        """Assign custom root certificates used for TLS verification."""
        self._root_certificates = root_certificates
        if self._channel and self._address._is_transport_security():
            self._close()

    def _set_verify_certificates(self, verify: bool):
        """Set whether TLS certificates should be verified."""
        if self._verify_certificates == verify:
            return

        self._verify_certificates = verify

        if verify and self._channel and self._address._is_transport_security():
            # Force channel recreation to ensure certificates are revalidated.
            self._close()

    def _build_channel_options(self):
        """
        Build gRPC channel options for TLS connections.

        The options `grpc.default_authority` and `grpc.ssl_target_name_override`
        are intentionally set to a fixed value ("127.0.0.1") to bypass standard
        TLS hostname verification.

        This is REQUIRED because Hedera nodes are connected to via IP addresses
        from the address book, while their TLS certificates are not issued for
        those IPs. As a result, standard hostname verification would fail even
        for legitimate nodes.

        Although hostname verification is disabled, transport security is NOT
        weakened. Instead of relying on hostnames, the SDK validates the server
        by performing certificate hash pinning. This guarantees the client is
        communicating with the correct Hedera node regardless of the hostname
        or IP address used to connect.
        """
        return [
            ("grpc.default_authority", "127.0.0.1"),
            ("grpc.ssl_target_name_override", "127.0.0.1"),
            ("grpc.keepalive_time_ms", 100000),
            ("grpc.keepalive_timeout_ms", 10000),
            ("grpc.keepalive_permit_without_calls", 1),
        ]

    def _resolve_trust_anchor(self) -> bytes | None:
        """
        Resolve the address-book certificate hash used to pin fetched certificates.

        Returns:
            bytes | None: The address-book certificate hash, or None if the node
            has no address book.
        """
        if self._address_book is not None:
            return self._address_book.cert_hash

        return None

    def _has_trust_anchor(self) -> bool:
        """
        Whether this node can authenticate the server when verification is enabled.

        A trust anchor exists when explicitly configured root certificates are
        present, allowing the TLS stack to validate the server against them,
        or when the address book supplies a non-empty certificate hash to pin the fetched certificate.
        """
        if bool(self._root_certificates and self._root_certificates.strip()):
            return True

        cert_hash = self._resolve_trust_anchor()
        return bool(_normalize_cert_hash(cert_hash))

    def _validate_tls_certificate_with_trust_manager(self):
        """
        Validate the remote TLS certificate using HederaTrustManager.
        This performs a pre-handshake validation by fetching the server certificate
        and comparing its hash to the expected hash from the address book.

        Raises:
            ValueError: If verification is enabled but no trust anchor exists
                (no address-book certificate hash and no explicitly configured
                root certificates), or if the certificate hash does not match.
        """
        if not self._address._is_transport_security() or not self._verify_certificates:
            return

        # Explicitly configured root certificates are a complete trust anchor:
        # the TLS stack authenticates the server against them, so certificate
        # hash pinning does not apply.
        if self._root_certificates:
            return

        if not self._has_trust_anchor():
            raise ValueError(_NO_TRUST_ANCHOR_MESSAGE)

        cert_hash = self._resolve_trust_anchor()

        # Create trust manager and validate certificate
        trust_manager = _HederaTrustManager(cert_hash, self._verify_certificates)
        trust_manager.check_server_trusted(self._node_pem_cert)

    def _fetch_server_certificate_pem(self) -> bytes | None:
        """
        Perform a TLS handshake and retrieve the server certificate in PEM format.

        Returns:
            bytes: PEM-encoded certificate bytes, or None if the handshake could
            not be completed (e.g. the node is unreachable, there is no TLS
            listener on the port, or no certificate is presented).
        """
        host = self._address._get_host()
        port = self._address._get_port()
        server_hostname = host

        # Create TLS context that accepts any certificate (we validate hash ourselves)
        context = ssl.create_default_context()
        # Restrict SSL/TLS versions to TLSv1.2+ only for security
        if hasattr(context, "minimum_version") and hasattr(ssl, "TLSVersion"):
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:
            # Backwards compatibility for Python <3.7 that lacks minimum_version
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        try:
            with (
                socket.create_connection((host, port), timeout=CERT_FETCH_TIMEOUT_SECONDS) as sock,
                context.wrap_socket(sock, server_hostname=server_hostname) as tls_socket,
            ):
                der_cert = tls_socket.getpeercert(True)
        except OSError as e:
            logger.warning("Failed to fetch server certificate from %s:%s: %s", host, port, e)
            return None

        # Convert DER to PEM format (matching Java's PEM encoding)
        return ssl.DER_cert_to_PEM_cert(der_cert).encode("utf-8")

    def is_healthy(self) -> bool:
        """
        Determine whether this node is currently eligible for use.

        A node is considered healthy if the current time is greater than or equal
        to its scheduled readmission time (`_readmit_time`). Nodes
        """
        return self._readmit_time <= time.monotonic()

    def _increase_backoff(self) -> None:
        """Increase the node's backoff duration after a failure."""
        self._bad_grpc_response_count += 1
        self._current_backoff = min(self._current_backoff * 2, self._max_backoff)
        self._readmit_time = time.monotonic() + self._current_backoff

    def _decrease_backoff(self) -> None:
        """Decrease the node's backoff duration after a successful operation."""
        self._current_backoff = max(self._current_backoff / 2, self._min_backoff)
