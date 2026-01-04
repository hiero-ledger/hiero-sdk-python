"""
Unit tests for Client factory methods (from_env, for_testnet, for_mainnet, for_previewnet).
"""

import os
import pytest
from unittest.mock import patch

from hiero_sdk_python.client import client as client_module

from hiero_sdk_python import (
    Client,
    AccountId, 
    PrivateKey 
)

@pytest.mark.parametrize(
    "factory_method, expected_network",
    [
        (Client.for_testnet, "testnet"),
        (Client.for_mainnet, "mainnet"),
        (Client.for_previewnet, "previewnet"),
    ],
)
def test_factory_basic_setup(factory_method, expected_network):
    """Test that factory methods return a Client with correct network and no operator."""
    client = factory_method()
    
    assert isinstance(client, Client)
    assert client.network.network == expected_network
    assert client.operator_account_id is None
    assert client.operator_private_key is None
    
    client.close()

def test_for_testnet_then_set_operator():
    """Test that we can manually set the operator on a factory client."""
    client = Client.for_testnet()
    
    # Generate dummy credentials
    operator_id = AccountId(0, 0, 12345)
    operator_key = PrivateKey.generate_ed25519()
    
    client.set_operator(operator_id, operator_key)
    
    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()
    assert client.operator is not None
    
    client.close()

def test_for_mainnet_then_set_operator():
    """Test that we can manually set the operator on a mainnet client."""
    client = Client.for_mainnet()
    
    operator_id = AccountId(0, 0, 67890)
    operator_key = PrivateKey.generate_ecdsa()

    client.set_operator(operator_id, operator_key)
    
    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()
    
    client.close()

def test_from_env_missing_operator_id_raises_error():
    """Test that from_env raises ValueError when OPERATOR_ID is missing."""
    dummy_key = PrivateKey.generate_ed25519().to_string_der()
    
    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, {"OPERATOR_KEY": dummy_key}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Client.from_env()
            assert "OPERATOR_ID" in str(exc_info.value)

def test_from_env_missing_operator_key_raises_error():
    """Test that from_env raises ValueError when OPERATOR_KEY is missing."""
    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, {"OPERATOR_ID": "0.0.1234"}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Client.from_env()
            assert "OPERATOR_KEY" in str(exc_info.value)

def test_from_env_with_valid_credentials():
    """Test that from_env creates client with valid environment variables."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key_str,
    }

    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert isinstance(client, Client)
            assert client.operator_account_id == AccountId.from_string("0.0.1234")
            client.close()

def test_from_env_with_explicit_network_parameter():
    """Test that from_env uses explicit network parameter over env var."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.5678",
        "OPERATOR_KEY": test_key_str,
        "NETWORK": "testnet",
    }

    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env(network="mainnet")
            assert client.network.network == "mainnet"
            client.close()

def test_from_env_defaults_to_testnet():
    """Test that from_env defaults to testnet when NETWORK not set."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1111",
        "OPERATOR_KEY": test_key_str,
    }

    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert client.network.network == "testnet"
            client.close()

def test_from_env_uses_network_env_var():
    """Test that from_env uses NETWORK env var when no argument is provided."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key_str,
        "NETWORK": "previewnet",
    }

    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert client.network.network == "previewnet"
            client.close()

def test_from_env_with_invalid_network_name():
    """Test that from_env raises error for invalid network name."""
    test_key = PrivateKey.generate_ed25519()
    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key.to_string_der(),
    }
    
    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid network name"):
                Client.from_env(network="mars_network")

def test_from_env_with_malformed_operator_id():
    """Test that from_env raises error for malformed OPERATOR_ID."""
    test_key = PrivateKey.generate_ed25519()
    env_vars = {
        "OPERATOR_ID": "not-an-account-id",
        "OPERATOR_KEY": test_key.to_string_der(),
    }
    
    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid account ID"):
                Client.from_env()

def test_from_env_with_malformed_operator_key():
    """Test that from_env raises error for malformed OPERATOR_KEY."""
    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": "not-a-valid-key",
    }
    
    with patch.object(client_module, 'load_dotenv'):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                Client.from_env()