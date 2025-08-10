import pytest
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams, TokenKeys
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from tests.integration.utils_for_test import IntegrationTestEnv

@pytest.mark.integration
def test_token_create_with_custom_fee_e2e():
    env = IntegrationTestEnv()

    try:
        custom_fee = CustomFixedFee(
            amount=10,
            denominating_token_id=TokenId(0, 0, 0),  # HBAR
            fee_collector_account_id=env.operator_id,
        )

        token_params = TokenParams(
            token_name="Test Token with Fee",
            token_symbol="FEE",
            treasury_account_id=env.operator_id,
            initial_supply=1000,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
            custom_fees=[custom_fee],
        )

        keys = TokenKeys(admin_key=env.operator_key, supply_key=env.operator_key)

        transaction = (
            TokenCreateTransaction(token_params=token_params, keys=keys)
            .freeze_with(env.client)
            .sign(env.operator_key)
        )

        receipt = transaction.execute(env.client)

        assert receipt.token_id is not None
        token_id = receipt.token_id

        # Query for the token info to verify the custom fee
        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

        assert len(token_info.custom_fees) == 1
        retrieved_fee = token_info.custom_fees[0]

        assert isinstance(retrieved_fee, CustomFixedFee)
        assert retrieved_fee.amount == 10
        assert retrieved_fee.fee_collector_account_id == env.operator_id
    finally:
        env.close()