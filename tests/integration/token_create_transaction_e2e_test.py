import datetime
import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token


@pytest.mark.integration
def test_integration_fungible_token_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
    finally:
        env.close()


@pytest.mark.integration
def test_integration_nft_token_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_nft_token(env)
        
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_sets_default_autorenew_values():
    """Test that when no expiration_time or auto_renew_account is explicitly provided default values are set"""
    env = IntegrationTestEnv()
    try:
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON,
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None, "TokenID not found in receipt. Token may not have been created."

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.auto_renew_period == Duration(7890000), "Token auto renew period mismatch"
        assert token_info.auto_renew_account == env.client.operator_account_id, "Token auto renew account mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_with_expiration_time():
    """Test create fungible token with expiration_time"""
    env = IntegrationTestEnv()
    try:
        expiration_time = Timestamp.from_date(datetime.datetime.now() + datetime.timedelta(days=30))
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            expiration_time=expiration_time,
            token_type=TokenType.FUNGIBLE_COMMON
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None, "TokenID not found in receipt. Token may not have been created."
    
        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)

        assert token_info.expiry.seconds == expiration_time.seconds, "Token expiry mismatch" 
        assert token_info.auto_renew_period == Duration(0)
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_auto_assigns_account_if_autorenew_period_present():
    """
    Test that if an auto_renew_period is set but auto_renew_account is not set 
    it get automatically assigns the client's operator account or transaction_id account_id.
    """
    env = IntegrationTestEnv()

    try:
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON,
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None,"TokenID not found in receipt. Token may not have been created."

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.auto_renew_period == Duration(7890000), "Token auto renew period mismatch" # Defaut around ~90 days
        # Client operator account if no auto_renew_account set
        assert token_info.auto_renew_account == env.client.operator_account_id, "Token auto renew account missmatch"
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_with_fee_schedule_key():
    """
    Test create fungible token with fee_schedule_key
    """
    env = IntegrationTestEnv()

    try:
        fee_schedule_key = PrivateKey.generate()
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON
        )

        receipt = (
            TokenCreateTransaction(params)
            .set_fee_schedule_key(fee_schedule_key)
            .freeze_with(env.client)
            .execute(env.client)
        )
        assert receipt.token_id is not None

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.fee_schedule_key.to_string() == fee_schedule_key.public_key().to_string(), "Fee schedule key missmatch"

        # Validate Fee schedule key
        # TODO (required TokenFeeScheduleUpdateTransaction)
    finally:
        env.close()
