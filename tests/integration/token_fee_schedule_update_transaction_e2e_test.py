import pytest
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams, TokenKeys
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_token_fee_schedule_update_fails_no_fee_schedule_key():
    """Test that updating fee schedule fails when token has no fee schedule key."""
    env = IntegrationTestEnv()

    try:
        token_params = TokenParams(
            token_name="Fee Schedule Test Token",
            token_symbol="FSTT",
            treasury_account_id=env.operator_id,
            initial_supply=1000,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
        )

        keys = TokenKeys(
            admin_key=env.operator_key,
            supply_key=env.operator_key
        )

        create_transaction = (
            TokenCreateTransaction(token_params=token_params, keys=keys)
            .freeze_with(env.client)
            .sign(env.operator_key)
        )

        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode(create_receipt.status).name}"
        token_id = create_receipt.token_id

        assert token_id is not None

        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert len(token_info.custom_fees) == 0

        fixed_fee = CustomFixedFee(
            amount=10,
            fee_collector_account_id=env.operator_id,
        )

        update_transaction = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([fixed_fee])
            .freeze_with(env.client)
            .sign(env.operator_key)
        )

        update_receipt = update_transaction.execute(env.client)
        assert update_receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY, f"Fee schedule update should have failed with TOKEN_HAS_NO_FEE_SCHEDULE_KEY status but got: {ResponseCode(update_receipt.status).name}"

    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_with_existing_custom_fees():
    """Test fee schedule update on a token that was created with custom fees."""
    env = IntegrationTestEnv()

    try:
        initial_custom_fee = CustomFixedFee(
            amount=5,
            fee_collector_account_id=env.operator_id,
        )

        token_params = TokenParams(
            token_name="Fee Token With Custom Fees",
            token_symbol="FTWCF",
            treasury_account_id=env.operator_id,
            initial_supply=1000,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
            custom_fees=[initial_custom_fee],
        )

        keys = TokenKeys(
            admin_key=env.operator_key,
            supply_key=env.operator_key
        )

        create_transaction = (
            TokenCreateTransaction(token_params=token_params, keys=keys)
            .freeze_with(env.client)
            .sign(env.operator_key)
        )

        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode(create_receipt.status).name}"
        token_id = create_receipt.token_id

        assert token_id is not None

        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert len(token_info.custom_fees) == 1
        assert isinstance(token_info.custom_fees[0], CustomFixedFee)
        assert token_info.custom_fees[0].amount == 5

        new_fixed_fee = CustomFixedFee(
            amount=15,
            fee_collector_account_id=env.operator_id,
        )

        update_transaction = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fixed_fee])
            .freeze_with(env.client)
            .sign(env.operator_key)
        )

        update_receipt = update_transaction.execute(env.client)
        
        if update_receipt.status == ResponseCode.SUCCESS:
            updated_token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
            assert len(updated_token_info.custom_fees) == 1
            assert updated_token_info.custom_fees[0].amount == 15
        else:
            assert update_receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY, f"Expected TOKEN_HAS_NO_FEE_SCHEDULE_KEY but got: {ResponseCode(update_receipt.status).name}"

    finally:
        env.close()