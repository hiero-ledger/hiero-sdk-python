import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_key_sign_and_verify():
    """
    Test that we can sign a transaction using a key extracted from the Key object.
    
    This test demonstrates:
    1. Creating a Key object from a generated private key
    2. Using the private key from the Key object to sign a transaction
    3. Verifying the transaction executes successfully
    """
    env = IntegrationTestEnv()
    
    try:
        # Generate a new private key and wrap it in a Key object
        new_private_key = PrivateKey.generate("ed25519")
        key = Key(new_private_key)
        
        # Verify the key is recognized as a private key
        assert key.is_private, "Key should be recognized as private"
        
        # Extract the private key from the Key object
        private_key_from_key = key.private_key
        
        # Get the public key to create a new account
        public_key = key.public_key
        
        # Create a new account with the public key
        account_transaction = AccountCreateTransaction(
            key=public_key,
            initial_balance=Hbar(1),
            memo="Test Account for Key Signing"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None, "Account ID should not be None"
        
        # Now test signing a transaction with the key extracted from the Key object
        # Create a transfer transaction that requires signing from the new account
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(account_id, -100000)  # Withdraw from new account
        transfer_transaction.add_hbar_transfer(env.operator_id, 100000)  # Send to operator
        
        # Freeze and sign with the private key extracted from the Key object
        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(private_key_from_key)
        
        receipt = transfer_transaction.execute(env.client)
        
        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
        
    finally:
        env.close()

@pytest.mark.integration
def test_set_key():
    """
    Test that we can set a key extracted from the Key object when creating a token.
    Uses the public property: key.private_key
    """
    env = IntegrationTestEnv()
    
    try:
        # Create a Key object from the operator's private key
        key = Key(env.operator_key)
        
        # Create token using key extracted from the Key object
        token_params = TokenParams(
            token_name="KeyTestToken",
            token_symbol="KTT",
            decimals=2,
            initial_supply=1000,
            treasury_account_id=env.operator_id,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=10000
        )
        
        # Extract the key using the public property
        token_keys = TokenKeys(
            admin_key=key.private_key,  # Use the public property
            supply_key=key.private_key
        )
        
        token_transaction = TokenCreateTransaction(token_params, token_keys)
        token_receipt = token_transaction.execute(env.client)
        
        assert token_receipt.status == ResponseCode.SUCCESS
        assert token_receipt.token_id is not None
        
    finally:
        env.close()



