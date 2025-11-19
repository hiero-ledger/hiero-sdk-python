import pytest
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_account_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        initial_balance = Hbar(2)
        
        assert initial_balance.to_tinybars() == 200000000
        
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."
    finally:
        env.close()
    
    
    