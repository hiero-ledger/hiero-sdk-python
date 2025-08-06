import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_mint_nft_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(2)
        
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        metadata = [b"NFT Token A", b"NFT Token B"]
        mint_transaction = TokenMintTransaction(
            token_id=token_id,
            metadata=metadata
        )
        
        mint_transaction.freeze_with(env.client)
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT token minting failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 


@pytest.mark.integration
def test_integration_token_mint_fungible_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(2)
        
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        mint_transaction = TokenMintTransaction(
            token_id=token_id,
            amount=2000
        )
        
        mint_transaction.freeze_with(env.client)
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token minting failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 
