import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token

@pytest.mark.integration
def test_token_grant_kyc_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create a new account
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(2))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id

        # Create a new token and set the kyc key to be the operator's key
        token_id = create_fungible_token(env, [lambda tx: tx.set_kyc_key(env.operator_key)])
        
        # Associate the token to the new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account_private_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Grant KYC to the new account
        receipt = (
            TokenGrantKycTransaction()
            .set_account_id(account_id)
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token grant KYC failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_grant_kyc_transaction_fails_with_no_kyc_key():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create a new account
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(2))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id
        
        # Create a new token without KYC key
        token_id = create_fungible_token(env)
        
        # Associate the token to the new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account_private_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Try to grant KYC for token without KYC key - should fail with TOKEN_HAS_NO_KYC_KEY
        receipt = (
            TokenGrantKycTransaction()
            .set_account_id(account_id)
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.TOKEN_HAS_NO_KYC_KEY, f"Token grant KYC should have failed with TOKEN_HAS_NO_KYC_KEY status but got: {ResponseCode(receipt.status).name}"
        
        # Try to grant KYC with non-KYC key - should fail with TOKEN_HAS_NO_KYC_KEY
        receipt = (
            TokenGrantKycTransaction()
            .set_account_id(account_id)
            .set_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account_private_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.TOKEN_HAS_NO_KYC_KEY, f"Token grant KYC should have failed with TOKEN_HAS_NO_KYC_KEY status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()
        
@pytest.mark.integration
def test_token_grant_kyc_transaction_fails_when_account_not_associated():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create a new account
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(2))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id
        
        # Create a new token and set the kyc key to be the operator's key
        token_id = create_fungible_token(env, [lambda tx: tx.set_kyc_key(env.operator_key)])
        
        # Grant KYC to the new account - should fail with ACCOUNT_NOT_ASSOCIATED_TO_TOKEN
        receipt = (
            TokenGrantKycTransaction()
            .set_account_id(account_id)
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.TOKEN_NOT_ASSOCIATED_TO_ACCOUNT, f"Token grant KYC should have failed with TOKEN_NOT_ASSOCIATED_TO_ACCOUNT status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()