import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_unfreeze_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(2)
        
        assert initial_balance.to_tinybars() == 200000000
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        account_transaction.freeze_with(env.client)
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        assert account_id is not None
        
        token_id = create_fungible_token(env)
        
        assert token_id is not None
        
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
            
        freeze_transaction = TokenFreezeTransaction(
            token_id=token_id,
            account_id=account_id
        )
        freeze_transaction.freeze_with(env.client)
        receipt = freeze_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token freeze failed with status: {ResponseCode(receipt.status).name}"
        
        unfreeze_transaction = TokenUnfreezeTransaction(
            token_id=token_id,
            account_id=account_id
        )
        
        unfreeze_transaction.freeze_with(env.client)
        receipt = unfreeze_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token unfreeze failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close()