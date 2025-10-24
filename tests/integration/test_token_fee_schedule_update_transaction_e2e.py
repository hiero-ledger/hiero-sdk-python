import pytest


from tests.integration.utils_for_test import IntegrationTestEnv
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode

from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)


@pytest.mark.integration
def test_token_fee_schedule_update_e2e():
    """
    Tests that a token's fee schedule can be updated in a live test.
    1. Creates a new token with an admin key and an initial fee.
    2. Uses TokenFeeScheduleUpdateTransaction to change that fee.
    3. Queries the token to confirm the fee was changed.
    """
    env = IntegrationTestEnv()

    try:
        # --- Step 1: Create a token WITH an admin key and an initial fee ---
        
        initial_fee = CustomFixedFee(
            amount=10,  # 10 tinybar fee
            fee_collector_account_id=env.operator_id,
        )

        token_params = TokenParams(
            token_name="Test Token",
            token_symbol="TEST",
            treasury_account_id=env.operator_id,
            initial_supply=1000,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
            custom_fees=[initial_fee],  # Set initial fee
        )

        # IMPORTANT: Must set admin_key to be able to update
        keys = TokenKeys(
            admin_key=env.operator_key, supply_key=env.operator_key
        )

        create_tx = (
            TokenCreateTransaction(token_params=token_params, keys=keys)
            .freeze_with(env.client)
            .sign(env.operator_key)  # Admin key must sign
        )

        create_receipt = create_tx.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS
        token_id = create_receipt.token_id
        assert token_id is not None

        # --- Step 2: Update the fee schedule with new transaction ---

        # Define a *new* fee schedule
        new_fee = CustomFixedFee(
            amount=25,  # New fee is 25 tinybar
            fee_collector_account_id=env.operator_id,
        )
        new_fee_list = [new_fee]

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees(new_fee_list)
            .freeze_with(env.client)
            .sign(env.operator_key)  # Admin key MUST sign
        )

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.SUCCESS

        # --- Step 3: Query the token to verify the fee was updated ---
        
        token_info = (
            TokenInfoQuery().set_token_id(token_id).execute(env.client)
        )

        assert len(token_info.custom_fees) == 1
        retrieved_fee = token_info.custom_fees[0]

        assert isinstance(retrieved_fee, CustomFixedFee)
        # Assert the *new* amount
        assert retrieved_fee.amount == 25
        assert retrieved_fee.fee_collector_account_id == env.operator_id

    finally:
        env.close()
