import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_transfer_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(2)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        account_transaction.freeze_with(env.client)
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}"
        
        account_id = receipt.accountId
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
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode.get_name(receipt.status)}"
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.operator_id, -1)
        transfer_transaction.add_token_transfer(token_id, account_id, 1)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode.get_name(receipt.status)}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance is not None
    except Exception as e:
        pytest.fail(f"Token transfer test failed: {str(e)}")
    finally:
        env.close(token_id)