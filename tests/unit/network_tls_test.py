"""Unit tests for TLS configuration in Network and Client."""

import pytest
from src.hiero_sdk_python.client.client import Client
from src.hiero_sdk_python.client.network import Network
from src.hiero_sdk_python.account.account_id import AccountId
from src.hiero_sdk_python.node import _Node

pytestmark = pytest.mark.unit


def test_network_tls_enabled_by_default_for_hosted_networks():
    """Test that TLS is enabled by default for hosted networks."""
    for network_name in ("mainnet", "testnet", "previewnet"):
        network = Network(network_name)
        assert (
            network.is_transport_security() is True
        ), f"TLS should be enabled for {network_name}"


def test_network_tls_disabled_by_default_for_local_networks():
    """Test that TLS is disabled by default for local networks."""
    for network_name in ("solo", "localhost", "local"):
        network = Network(network_name)
        assert (
            network.is_transport_security() is False
        ), f"TLS should be disabled for {network_name}"


def test_network_tls_disabled_by_default_for_custom_networks():
    """Test that TLS is disabled by default for custom networks."""
    # Provide nodes for custom network since it has no defaults
    from src.hiero_sdk_python.node import _Node

    nodes = [_Node(AccountId(0, 0, 3), "127.0.0.1:50211", None)]
    network = Network("custom-network", nodes=nodes)
    assert network.is_transport_security() is False


def test_network_verification_enabled_by_default():
    """Test that certificate verification is enabled by default for all networks."""
    for network_name in ("mainnet", "testnet", "previewnet", "solo", "localhost"):
        network = Network(network_name)
        assert (
            network.is_verify_certificates() is True
        ), f"Verification should be enabled for {network_name}"


def test_network_set_transport_security_enable():
    """Test enabling TLS on network."""
    network = Network("solo")  # Starts with TLS disabled
    assert network.is_transport_security() is False

    network.set_transport_security(True)
    assert network.is_transport_security() is True

    # Verify all nodes are updated
    for node in network.nodes:
        assert node._address._is_transport_security() is True


def test_network_set_transport_security_disable():
    """Test disabling TLS on network."""
    network = Network("testnet")  # Starts with TLS enabled
    assert network.is_transport_security() is True

    network.set_transport_security(False)
    assert network.is_transport_security() is False

    # Verify all nodes are updated
    for node in network.nodes:
        assert node._address._is_transport_security() is False


def test_network_set_transport_security_idempotent():
    """Test that setting TLS to same value is idempotent."""
    network = Network("testnet")
    initial_state = network.is_transport_security()

    # Set to same value multiple times
    network.set_transport_security(initial_state)
    network.set_transport_security(initial_state)
    network.set_transport_security(initial_state)

    assert network.is_transport_security() == initial_state


def test_network_set_verify_certificates():
    """Test setting certificate verification."""
    network = Network("testnet")
    assert network.is_verify_certificates() is True

    network.set_verify_certificates(False)
    assert network.is_verify_certificates() is False

    # Verify all nodes are updated
    for node in network.nodes:
        assert node._verify_certificates is False


def test_network_set_verify_certificates_idempotent():
    """Test that setting verification to same value is idempotent."""
    network = Network("testnet")
    initial_state = network.is_verify_certificates()

    network.set_verify_certificates(initial_state)
    network.set_verify_certificates(initial_state)

    assert network.is_verify_certificates() == initial_state


def test_network_set_tls_root_certificates():
    """Test setting custom root certificates."""
    network = Network("testnet")
    custom_certs = b"-----BEGIN CERTIFICATE-----\nCUSTOM\n-----END CERTIFICATE-----\n"

    network.set_tls_root_certificates(custom_certs)
    assert network.get_tls_root_certificates() == custom_certs

    # Verify all nodes are updated
    for node in network.nodes:
        assert node._root_certificates == custom_certs


def test_network_set_tls_root_certificates_none():
    """Test clearing custom root certificates."""
    network = Network("testnet")
    custom_certs = b"custom"
    network.set_tls_root_certificates(custom_certs)

    network.set_tls_root_certificates(None)
    assert network.get_tls_root_certificates() is None


def test_client_set_transport_security():
    """Test Client.set_transport_security() method."""
    network = Network("solo")
    client = Client(network)

    assert client.is_transport_security() is False
    client.set_transport_security(True)
    assert client.is_transport_security() is True

    # Should return self for chaining
    assert client.set_transport_security(False) is client


def test_client_set_verify_certificates():
    """Test Client.set_verify_certificates() method."""
    network = Network("testnet")
    client = Client(network)

    assert client.is_verify_certificates() is True
    client.set_verify_certificates(False)
    assert client.is_verify_certificates() is False

    # Should return self for chaining
    assert client.set_verify_certificates(True) is client


def test_client_set_tls_root_certificates():
    """Test Client.set_tls_root_certificates() method."""
    network = Network("testnet")
    client = Client(network)
    custom_certs = b"custom_certs"

    client.set_tls_root_certificates(custom_certs)
    assert client.get_tls_root_certificates() == custom_certs


def test_network_get_mirror_rest_url_hosted_networks():
    """Test REST URL generation for hosted networks."""
    for network_name in ("mainnet", "testnet", "previewnet"):
        network = Network(network_name)
        url = network.get_mirror_rest_url()
        assert url.startswith("https://")
        assert url.endswith("/api/v1")
        # Should not include :443 for default HTTPS port
        assert ":443" not in url


def test_network_get_mirror_rest_url_localhost():
    """Test REST URL generation for localhost."""
    network = Network("solo")
    url = network.get_mirror_rest_url()
    # Solo uses http://localhost:5551
    assert "http://" in url or "https://" in url
    assert url.endswith("/api/v1")


def test_network_get_mirror_rest_url_custom_port():
    """Test REST URL generation with custom port for network without MIRROR_NODE_URLS entry."""
    # Use a custom network that doesn't have MIRROR_NODE_URLS entry
    from src.hiero_sdk_python.node import _Node

    nodes = [_Node(AccountId(0, 0, 3), "127.0.0.1:50211", None)]
    network = Network(
        "custom-network", nodes=nodes, mirror_address="custom.mirror.com:8443"
    )
    url = network.get_mirror_rest_url()
    # Should use custom mirror_address and include port
    assert url.startswith("https://custom.mirror.com:8443/api/v1")
