import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_wipe_transaction import TokenWipeTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_wipe_account_transaction_can_execute():
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
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)
        transfer_transaction.add_token_transfer(token_id, account_id, 10)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
        
        wipe_transaction = TokenWipeTransaction(
            token_id=token_id,
            account_id=account_id,
            amount=10
        )
        
        wipe_transaction.freeze_with(env.client)
        receipt = wipe_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token wipe failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 0
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_wipe_transaction_no_token_id():
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
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)
        transfer_transaction.add_token_transfer(token_id, account_id, 10)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
        
        wipe_transaction = TokenWipeTransaction(
            token_id=None,
            account_id=account_id,
            amount=10
        )
       
        wipe_transaction.freeze_with(env.client)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_TOKEN_ID"):
            wipe_transaction.execute(env.client)
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_wipe_transaction_no_account_id():
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
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)
        transfer_transaction.add_token_transfer(token_id, account_id, 10)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
        
        wipe_transaction = TokenWipeTransaction(
            token_id=token_id,
            account_id=None,
            amount=10
        )
       
        wipe_transaction.freeze_with(env.client)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_ACCOUNT_ID"):
            wipe_transaction.execute(env.client)
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_wipe_transaction_no_amount():
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
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)
        transfer_transaction.add_token_transfer(token_id, account_id, 10)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
        
        wipe_transaction = TokenWipeTransaction(
            token_id=token_id,
            account_id=account_id,
            amount=0
        )
       
        wipe_transaction.freeze_with(env.client)
        receipt = wipe_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token wipe failed with status: {ResponseCode(receipt.status).name}"

        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
    finally:
        env.close()
        

@pytest.mark.integration
def test_integration_token_wipe_account_transaction_not_zero_tokens_at_delete():
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
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -20)
        transfer_transaction.add_token_transfer(token_id, account_id, 20)
        
        transfer_transaction.freeze_with(env.client)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 20
        
        wipe_transaction = TokenWipeTransaction(
            token_id=token_id,
            account_id=account_id,
            amount=10
        )
        
        wipe_transaction.freeze_with(env.client)
        receipt = wipe_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token wipe failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance.token_balances is not None and balance.token_balances[token_id] == 10
    finally:
        env.close()