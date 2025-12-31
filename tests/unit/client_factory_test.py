"""
Unit tests for Client factory methods (from_env, for_testnet, for_mainnet, for_previewnet).
"""

import os
import pytest
from unittest.mock import patch

# IMPORTANT: Import from the module where load_dotenv is used to patch it correctly
from hiero_sdk_python.client import client as client_module 
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

class TestClientForTestnet:
    """Tests for Client.for_testnet() class method."""

    def test_for_testnet_returns_client(self):
        client = Client.for_testnet()
        assert isinstance(client, Client)
        client.close()

    def test_for_testnet_network_is_testnet(self):
        client = Client.for_testnet()
        assert client.network.network == "testnet"
        client.close()

    def test_for_testnet_operator_not_set(self):
        client = Client.for_testnet()
        assert client.operator_account_id is None
        assert client.operator_private_key is None
        client.close()


class TestClientForMainnet:
    """Tests for Client.for_mainnet() class method."""

    def test_for_mainnet_returns_client(self):
        client = Client.for_mainnet()
        assert isinstance(client, Client)
        client.close()

    def test_for_mainnet_network_is_mainnet(self):
        client = Client.for_mainnet()
        assert client.network.network == "mainnet"
        client.close()

    def test_for_mainnet_operator_not_set(self):
        client = Client.for_mainnet()
        assert client.operator_account_id is None
        client.close()


class TestClientForPreviewnet:
    """Tests for Client.for_previewnet() class method."""

    def test_for_previewnet_returns_client(self):
        client = Client.for_previewnet()
        assert isinstance(client, Client)
        client.close()

    def test_for_previewnet_network_is_previewnet(self):
        client = Client.for_previewnet()
        assert client.network.network == "previewnet"
        client.close()

    def test_for_previewnet_operator_not_set(self):
        client = Client.for_previewnet()
        assert client.operator_account_id is None
        client.close()


class TestClientFromEnv:
    """Tests for Client.from_env() class method."""

    def test_from_env_missing_operator_id_raises_error(self):
        """Test that from_env raises ValueError when OPERATOR_ID is missing."""
        # Generate a real key to prevent validation errors
        dummy_key = PrivateKey.generate_ed25519().to_string_der()
        
        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, {"OPERATOR_KEY": dummy_key}, clear=True):
                with pytest.raises(ValueError) as exc_info:
                    Client.from_env()
                assert "OPERATOR_ID" in str(exc_info.value)

    def test_from_env_missing_operator_key_raises_error(self):
        """Test that from_env raises ValueError when OPERATOR_KEY is missing."""
        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, {"OPERATOR_ID": "0.0.1234"}, clear=True):
                with pytest.raises(ValueError) as exc_info:
                    Client.from_env()
                assert "OPERATOR_KEY" in str(exc_info.value)

    def test_from_env_missing_both_raises_error(self):
        """Test that from_env raises ValueError when both env vars are missing."""
        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError) as exc_info:
                    Client.from_env()
                assert "OPERATOR_ID" in str(exc_info.value)

    def test_from_env_with_valid_credentials(self):
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
                assert client.operator_private_key is not None
                assert client.network.network == "testnet"  # Default network
                client.close()

    def test_from_env_with_explicit_network_parameter(self):
        """Test that from_env uses explicit network parameter over env var."""
        test_key = PrivateKey.generate_ed25519()
        test_key_str = test_key.to_string_der()

        env_vars = {
            "OPERATOR_ID": "0.0.5678",
            "OPERATOR_KEY": test_key_str,
            "NETWORK": "testnet",  # Changed from HEDERA_NETWORK
        }

        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, env_vars, clear=True):
                client = Client.from_env(network="mainnet")

                assert client.network.network == "mainnet"
                client.close()

    def test_from_env_with_network_env_var(self):
        """Test that from_env uses NETWORK env var when no parameter given."""
        test_key = PrivateKey.generate_ed25519()
        test_key_str = test_key.to_string_der()

        env_vars = {
            "OPERATOR_ID": "0.0.9999",
            "OPERATOR_KEY": test_key_str,
            "NETWORK": "previewnet", # Changed from HEDERA_NETWORK
        }

        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, env_vars, clear=True):
                client = Client.from_env()

                assert client.network.network == "previewnet"
                client.close()

    def test_from_env_defaults_to_testnet(self):
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

    def test_from_env_network_case_insensitive(self):
        """Test that from_env handles network name case insensitively."""
        test_key = PrivateKey.generate_ed25519()
        test_key_str = test_key.to_string_der()

        env_vars = {
            "OPERATOR_ID": "0.0.2222",
            "OPERATOR_KEY": test_key_str,
            "NETWORK": "MAINNET", # Changed from HEDERA_NETWORK
        }

        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, env_vars, clear=True):
                client = Client.from_env()

                assert client.network.network == "mainnet"
                client.close()

    def test_from_env_sets_operator_correctly(self):
        """Test that from_env correctly sets operator on the client."""
        test_key = PrivateKey.generate_ed25519()
        test_key_str = test_key.to_string_der()

        env_vars = {
            "OPERATOR_ID": "0.0.3333",
            "OPERATOR_KEY": test_key_str,
        }

        with patch.object(client_module, 'load_dotenv'):
            with patch.dict(os.environ, env_vars, clear=True):
                client = Client.from_env()

                assert client.operator is not None
                assert client.operator.account_id == AccountId.from_string("0.0.3333")
                assert client.operator.private_key is not None
                client.close()