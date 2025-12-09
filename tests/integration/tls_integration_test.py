"""Integration tests for TLS functionality."""
import os
import pytest
from dotenv import load_dotenv

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from tests.integration.utils_for_test import IntegrationTestEnv

load_dotenv(override=True)

pytestmark = pytest.mark.integration


@pytest.mark.integration
def test_tls_enabled_by_default_for_testnet():
    """Test that TLS is enabled by default for testnet network."""
    network = Network('testnet')
    client = Client(network)
    
    try:
        # Verify TLS is enabled by default
        assert client.is_transport_security() is True, "TLS should be enabled by default for testnet"
        
        # Verify certificate verification is enabled by default
        assert client.is_verify_certificates() is True, "Certificate verification should be enabled by default"
        
        # Verify all nodes use TLS ports (50212)
        for node in network.nodes:
            assert node._address._is_transport_security() is True, f"Node {node._account_id} should use TLS port"
            assert node._address._get_port() == 50212, f"Node {node._account_id} should use port 50212 for TLS"
        
            # Note: Query execution over TLS requires proper certificate setup.
            # gRPC Python verifies certificates against the system CA store by default,
            # which may fail for testnet if certificates aren't in the system store.
            # Our custom verification (when enabled) validates against address book cert hashes.
            # For this test, we verify TLS configuration is correct without executing a query,
            # as query execution may fail due to system CA verification even when our
            # custom verification is disabled.
            
            # The test has already verified:
            # - TLS is enabled by default
            # - Certificate verification is enabled by default  
            # - All nodes use TLS port 50212
            # These are the key assertions for default TLS configuration.
    finally:
        client.close()


@pytest.mark.integration
def test_tls_enabled_by_default_for_mainnet():
    """Test that TLS is enabled by default for mainnet network."""
    network = Network('mainnet')
    client = Client(network)
    
    try:
        # Verify TLS is enabled by default
        assert client.is_transport_security() is True, "TLS should be enabled by default for mainnet"
        assert client.is_verify_certificates() is True, "Certificate verification should be enabled by default"
        
        # Verify all nodes use TLS ports
        for node in network.nodes:
            assert node._address._is_transport_security() is True, f"Node {node._account_id} should use TLS port"
            assert node._address._get_port() == 50212, f"Node {node._account_id} should use port 50212 for TLS"
    finally:
        client.close()


@pytest.mark.integration
def test_tls_disabled_by_default_for_localhost():
    """Test that TLS is disabled by default for localhost network."""
    network = Network('localhost')
    client = Client(network)
    
    try:
        # Verify TLS is disabled by default
        assert client.is_transport_security() is False, "TLS should be disabled by default for localhost"
        
        # Verify certificate verification is still enabled by default
        assert client.is_verify_certificates() is True, "Certificate verification should be enabled by default"
        
        # Verify all nodes use plaintext ports (50211)
        for node in network.nodes:
            assert node._address._is_transport_security() is False, f"Node {node._account_id} should use plaintext port"
            assert node._address._get_port() == 50211, f"Node {node._account_id} should use port 50211 for plaintext"
    finally:
        client.close()


@pytest.mark.integration
def test_tls_can_be_enabled_manually():
    """Test that TLS can be enabled manually on networks where it's disabled by default."""
    network = Network('localhost')
    client = Client(network)
    
    try:
        # Initially TLS should be disabled
        assert client.is_transport_security() is False, "TLS should be disabled by default for localhost"
        
        # Enable TLS manually
        client.set_transport_security(True)
        
        # Verify TLS is now enabled
        assert client.is_transport_security() is True, "TLS should be enabled after calling set_transport_security(True)"
        
        # Verify all nodes now use TLS ports
        for node in network.nodes:
            assert node._address._is_transport_security() is True, f"Node {node._account_id} should use TLS port after enabling"
            assert node._address._get_port() == 50212, f"Node {node._account_id} should use port 50212 for TLS"
    finally:
        client.close()


@pytest.mark.integration
def test_tls_can_be_disabled_manually():
    """Test that TLS can be disabled manually on networks where it's enabled by default."""
    network = Network('testnet')
    client = Client(network)
    
    try:
        # Initially TLS should be enabled
        assert client.is_transport_security() is True, "TLS should be enabled by default for testnet"
        
        # Disable TLS manually
        client.set_transport_security(False)
        
        # Verify TLS is now disabled
        assert client.is_transport_security() is False, "TLS should be disabled after calling set_transport_security(False)"
        
        # Verify all nodes now use plaintext ports
        for node in network.nodes:
            assert node._address._is_transport_security() is False, f"Node {node._account_id} should use plaintext port after disabling"
            assert node._address._get_port() == 50211, f"Node {node._account_id} should use port 50211 for plaintext"
    finally:
        client.close()


@pytest.mark.integration
def test_certificate_verification_can_be_disabled():
    """Test that certificate verification can be disabled while keeping TLS enabled."""
    network = Network('testnet')
    client = Client(network)
    
    try:
        # Initially verification should be enabled
        assert client.is_verify_certificates() is True, "Certificate verification should be enabled by default"
        assert client.is_transport_security() is True, "TLS should be enabled by default"
        
        # Disable verification
        client.set_verify_certificates(False)
        
        # Verify verification is disabled but TLS is still enabled
        assert client.is_verify_certificates() is False, "Certificate verification should be disabled"
        assert client.is_transport_security() is True, "TLS should still be enabled"
        
        # Verify all nodes reflect the change
        for node in network.nodes:
            assert node._verify_certificates is False, f"Node {node._account_id} should have verification disabled"
            assert node._address._is_transport_security() is True, f"Node {node._account_id} should still use TLS"
    finally:
        client.close()


@pytest.mark.integration
def test_tls_query_execution_with_verification():
    """Test executing a query over TLS with certificate verification enabled."""
    env = IntegrationTestEnv()
    
    try:
        # Get the actual network being used
        network_name = env.client.network.network
        
        # Enable TLS if not already enabled (for localhost/solo networks)
        if not env.client.is_transport_security():
            env.client.set_transport_security(True)
        
        # For verification to work, we need address books with cert hashes.
        # If nodes don't have address books, disable verification for this test.
        has_address_books = all(node._address_book is not None for node in env.client.network.nodes)
        
        if not has_address_books:
            # Disable verification if no address books available
            env.client.set_verify_certificates(False)
            pytest.skip("Address books with certificate hashes not available for verification test")
        
        # Verify TLS is enabled
        assert env.client.is_transport_security() is True, f"TLS should be enabled for {network_name}"
        
        # Execute a query over TLS
        balance_query = CryptoGetAccountBalanceQuery(account_id=env.operator_id)
        balance = balance_query.execute(env.client)
        
        # Explicitly verify the query succeeded
        assert balance is not None, "Balance query should return a result"
        assert balance.hbars is not None, "Balance should contain HBAR amount"
        
        # Verify the balance is a valid number (non-negative)
        assert balance.hbars.to_tinybars() >= 0, "Balance should be non-negative"
    finally:
        env.close()


@pytest.mark.integration
def test_tls_query_execution_without_verification():
    """Test executing a query over TLS with certificate verification disabled."""
    env = IntegrationTestEnv()
    
    try:
        # Get the actual network being used
        network_name = env.client.network.network
        
        # Skip if using localhost/solo as they may not have TLS properly configured
        if network_name in ('localhost', 'solo', 'local'):
            pytest.skip(f"TLS query execution test skipped for {network_name} network (TLS may not be properly configured)")
        
        # Enable TLS and disable verification
        env.client.set_transport_security(True)
        env.client.set_verify_certificates(False)
        
        # Verify settings
        assert env.client.is_transport_security() is True, "TLS should be enabled"
        assert env.client.is_verify_certificates() is False, "Certificate verification should be disabled"
        
        # Verify all nodes use TLS ports
        for node in env.client.network.nodes:
            assert node._address._is_transport_security() is True, f"Node {node._account_id} should use TLS port"
            assert node._address._get_port() == 50212, f"Node {node._account_id} should use port 50212 for TLS"
        
        # Execute a query over TLS without verification
        balance_query = CryptoGetAccountBalanceQuery(account_id=env.operator_id)
        balance = balance_query.execute(env.client)
        
        # Explicitly verify the query succeeded
        assert balance is not None, "Balance query should return a result"
        assert balance.hbars is not None, "Balance should contain HBAR amount"
    finally:
        env.close()


@pytest.mark.integration
def test_mirror_network_always_uses_tls():
    """Test that mirror network connections always use TLS."""
    network = Network('testnet')
    client = Client(network)
    
    try:
        # Verify mirror channel is created (it's created in __init__)
        assert client.mirror_channel is not None, "Mirror channel should be created"
        
        # Mirror channels always use secure_channel (TLS is mandatory)
        # We can't directly inspect the channel type, but we can verify
        # the mirror address uses port 443 (TLS port)
        mirror_address = network.get_mirror_address()
        assert ':443' in mirror_address or mirror_address.endswith(':443'), \
            f"Mirror address {mirror_address} should use port 443 for TLS"
        
        # Verify REST URL uses HTTPS
        rest_url = network.get_mirror_rest_url()
        assert rest_url.startswith('https://'), f"REST URL {rest_url} should use HTTPS"
        assert rest_url.endswith('/api/v1'), f"REST URL {rest_url} should end with /api/v1"
    finally:
        client.close()


@pytest.mark.integration
def test_tls_settings_persist_across_operations():
    """Test that TLS settings persist and are applied to all operations."""
    env = IntegrationTestEnv()
    
    try:
        # Get the actual network being used
        network_name = env.client.network.network
        
        # Skip if using localhost/solo as they may not have TLS properly configured
        if network_name in ('localhost', 'solo', 'local'):
            pytest.skip(f"TLS persistence test skipped for {network_name} network (TLS may not be properly configured)")
        
        # Check if nodes have address books for verification
        has_address_books = all(node._address_book is not None for node in env.client.network.nodes)
        
        # Set TLS configuration
        env.client.set_transport_security(True)
        
        # Only enable verification if address books are available
        if has_address_books:
            env.client.set_verify_certificates(True)
        else:
            env.client.set_verify_certificates(False)
        
        # Verify initial settings
        assert env.client.is_transport_security() is True, "TLS should be enabled"
        
        # Execute multiple queries to verify settings persist
        for i in range(3):
            balance_query = CryptoGetAccountBalanceQuery(account_id=env.operator_id)
            balance = balance_query.execute(env.client)
            
            # Verify each query succeeds
            assert balance is not None, f"Balance query {i+1} should return a result"
            assert balance.hbars is not None, f"Balance {i+1} should contain HBAR amount"
            
            # Verify TLS settings are still applied
            assert env.client.is_transport_security() is True, f"TLS should remain enabled after query {i+1}"
            
            # Verify nodes still use TLS ports
            for node in env.client.network.nodes:
                assert node._address._is_transport_security() is True, \
                    f"Node {node._account_id} should still use TLS port after query {i+1}"
                assert node._address._get_port() == 50212, \
                    f"Node {node._account_id} should use port 50212 after query {i+1}"
    finally:
        env.close()

