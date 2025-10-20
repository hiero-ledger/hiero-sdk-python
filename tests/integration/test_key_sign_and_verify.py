"""Integration tests for Key class signing and verification with Hedera network."""
import pytest
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from .utils_for_test import env


class TestKeySignAndVerify:
    """Integration tests for Key class with Hedera network operations."""

    def test_key_sign_and_verify(self):
        """Test that we can sign a transaction using a key extracted from the key object."""
        # Generate a new key pair
        private_key = PrivateKey.generate_ed25519()
        key = Key(private_key)
        
        # Test data to sign
        test_data = b"Hello, Hedera! This is a test message for signing."
        
        # Sign the data using the Key
        signature = key.sign(test_data)
        
        # Verify the signature using the same Key
        key.verify(signature, test_data)
        
        # Verify the signature using the public key directly
        public_key = key.public_key()
        public_key.verify(signature, test_data)

    def test_set_key(self, env):
        """Test we can set a key extracted from the key object, such as when creating a token."""
        if not env.operator_id or not env.operator_key:
            pytest.skip("Integration test requires operator account")
        
        # Generate a new key using the unified Key class
        admin_private_key = PrivateKey.generate_ed25519()
        admin_key = Key(admin_private_key)
        
        # Create token parameters
        token_params = TokenParams(
            token_name="TestKeyToken",
            token_symbol="TKT",
            decimals=2,
            initial_supply=1000,
            treasury_account_id=env.operator_id,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=10000
        )
        
        # Use the Key's public key for token keys
        token_keys = TokenKeys(
            admin_key=admin_key.public_key(),  # Extract public key from Key
            supply_key=env.operator_key,
            freeze_key=env.operator_key,
            wipe_key=env.operator_key
        )
        
        # Create the token
        token_transaction = TokenCreateTransaction(token_params, token_keys)
        token_receipt = token_transaction.execute(env.client)
        
        # Verify token creation was successful
        assert token_receipt.status == ResponseCode.SUCCESS
        assert token_receipt.token_id is not None

    def test_key_with_account_creation(self, env):
        """Test creating an account using a Key object."""
        if not env.operator_id or not env.operator_key:
            pytest.skip("Integration test requires operator account")
        
        # Generate a new key using the unified Key class
        account_private_key = PrivateKey.generate_ed25519()
        account_key = Key(account_private_key)
        
        # Create account using the Key's public key
        tx = (
            AccountCreateTransaction()
                .set_key(account_key.public_key())  # Extract public key from Key
                .set_initial_balance(Hbar(1.0))
        )
        
        receipt = tx.execute(env.client)
        
        # Verify account creation was successful
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.account_id is not None
        
        # Test that we can sign a transaction with the created key
        test_data = b"Account creation test data"
        signature = account_key.sign(test_data)
        account_key.verify(signature, test_data)

    def test_key_ecdsa_integration(self, env):
        """Test ECDSA key integration with Hedera operations."""
        if not env.operator_id or not env.operator_key:
            pytest.skip("Integration test requires operator account")
        
        # Generate an ECDSA key using the unified Key class
        ecdsa_private_key = PrivateKey.generate_ecdsa()
        ecdsa_key = Key(ecdsa_private_key)
        
        # Verify it's recognized as a private ECDSA key
        assert ecdsa_key.is_private
        assert ecdsa_key.private_key().is_ecdsa()
        
        # Test signing and verification
        test_data = b"ECDSA integration test data"
        signature = ecdsa_key.sign(test_data)
        ecdsa_key.verify(signature, test_data)
        
        # Create account using the ECDSA Key's public key
        tx = (
            AccountCreateTransaction()
                .set_key(ecdsa_key.public_key())
                .set_initial_balance(Hbar(0.5))
        )
        
        receipt = tx.execute(env.client)
        
        # Verify account creation was successful
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.account_id is not None

    def test_key_from_string_integration(self, env):
        """Test creating Key from string and using it in Hedera operations."""
        if not env.operator_id or not env.operator_key:
            pytest.skip("Integration test requires operator account")
        
        # Generate a key and convert to string
        original_private_key = PrivateKey.generate_ed25519()
        key_string = original_private_key.to_string()
        
        # Create Key from string
        key_from_string = Key.from_string(key_string)
        
        # Verify it's the same key
        assert key_from_string.is_private
        assert key_from_string.private_key().to_string() == key_string
        
        # Test signing with the reconstructed key
        test_data = b"Key from string test data"
        signature = key_from_string.sign(test_data)
        key_from_string.verify(signature, test_data)
        
        # Use it to create an account
        tx = (
            AccountCreateTransaction()
                .set_key(key_from_string.public_key())
                .set_initial_balance(Hbar(0.5))
        )
        
        receipt = tx.execute(env.client)
        
        # Verify account creation was successful
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.account_id is not None
