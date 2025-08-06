import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_associate_transaction_can_execute():
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
        account_receipt = account_transaction.execute(env.client)
        new_account_id = account_receipt.account_id
        
        token_id = create_fungible_token(env)
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
        
        associate_transaction = TokenAssociateTransaction(
            account_id=new_account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        associate_receipt = associate_transaction.execute(env.client)
        
        assert associate_receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(associate_receipt.status).name}"
    
        dissociate_transaction = TokenDissociateTransaction(
            account_id=new_account_id,
            token_ids=[token_id]
        )
        
        dissociate_transaction.freeze_with(env.client)
        dissociate_transaction.sign(new_account_private_key)
        dissociate_receipt = dissociate_transaction.execute(env.client)
        
        assert dissociate_receipt.status == ResponseCode.SUCCESS, f"Token dissociation failed with status: {ResponseCode(dissociate_receipt.status).name}"
    finally:
        env.close() 