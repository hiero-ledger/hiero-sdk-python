# tests/integration/test_integration_custom_fee.py

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt  

from tests.integration.utils_for_test import env, create_fungible_token, create_nft_token


@pytest.mark.integration
def test_custom_fee_can_execute_on_network(env):
    """
    Tests successful execution of a TokenCreateTransaction with a custom fee.
    Verifies base CustomFee fields (collector ID, exempt flag) are correctly
    serialized and retrieved from the Hedera network via TokenInfoQuery.
    """

    collector_account = env.create_account(initial_hbar=1.0)

    fixed_fee_amount = 50
    custom_fee = (
        CustomFixedFee(
            amount=fixed_fee_amount,
            denominated_token_id=None,
        )
        .set_fee_collector_account_id(collector_account.id)
        .set_all_collectors_are_exempt(False)
    )

    token_id = create_fungible_token(
        env,
        custom_fees=[custom_fee],
    )

    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert token_info is not None, "TokenInfoQuery returned None"
    assert len(token_info.custom_fees) == 1, "Expected exactly one custom fee"
    retrieved_fee = token_info.custom_fees[0]

    assert isinstance(retrieved_fee, CustomFixedFee), "Expected CustomFixedFee instance"
    assert retrieved_fee.fee_collector_account_id == collector_account.id
    assert retrieved_fee.all_collectors_are_exempt is False


@pytest.mark.integration
def test_custom_fee_collector_account_validation_on_network(env):
    """
    Tests that TokenCreateTransaction fails if CustomFee uses
    an invalid fee_collector_account_id. This indirectly verifies
    _validate_checksums logic on the network.
    """

    # Choose a high, non-existent AccountId (e.g., 0.0.999999999)
    non_existent_id = AccountId(shard=0, realm=0, num=999999999)

    custom_fee = (
        CustomFixedFee(amount=10, denominated_token_id=None)
        .set_fee_collector_account_id(non_existent_id)
        .set_all_collectors_are_exempt(False)
    )

    with pytest.raises(AssertionError) as excinfo:
      create_fungible_token(env, custom_fees=[custom_fee])

    assert "INVALID_CUSTOM_FEE_COLLECTOR" in str(
      excinfo.value
    ), f"Unexpected error message: {excinfo.value}"


@pytest.mark.integration
def test_custom_fractional_fee_dispatch_on_network(env):
    """
    Tests that a fractional fee is correctly dispatched from proto
    back into a CustomFractionalFee instance after querying the network.
    """

    collector_account = env.create_account(initial_hbar=1.0)

    numerator = 1
    denominator = 10
    min_amount = 5
    max_amount = 100

    custom_fee = (
        CustomFractionalFee(
            numerator=numerator,
            denominator=denominator,
            minimum_amount=min_amount,
            maximum_amount=max_amount,
        )
        .set_fee_collector_account_id(collector_account.id)
    )

    token_id = create_fungible_token(
        env,
        custom_fees=[custom_fee],
    )

    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert len(token_info.custom_fees) == 1, "Expected one fractional fee"
    retrieved_fee = token_info.custom_fees[0]

    assert isinstance(retrieved_fee, CustomFractionalFee), "Expected CustomFractionalFee instance"
    assert retrieved_fee.numerator == numerator
    assert retrieved_fee.denominator == denominator
    assert retrieved_fee.minimum_amount == min_amount
    assert retrieved_fee.maximum_amount == max_amount
    assert retrieved_fee.fee_collector_account_id == collector_account.id


@pytest.mark.integration
def test_custom_royalty_fee_dispatch_on_network(env):
    """
    Tests that a royalty fee with a fallback fee is correctly dispatched
    from proto back into a CustomRoyaltyFee instance after querying the network.
    """

    collector_account = env.create_account(initial_hbar=1.0)
    denominated_token_id = create_fungible_token(env)

    fallback_fee = CustomFixedFee(
        amount=5,
        denominated_token_id=denominated_token_id,
    )

    numerator = 2
    denominator = 100  # 2% royalty

    custom_fee = (
        CustomRoyaltyFee(
            numerator=numerator,
            denominator=denominator,
            fallback_fee=fallback_fee,
        )
        .set_fee_collector_account_id(collector_account.id)
    )

    token_id = create_nft_token(
        env,
        custom_fees=[custom_fee],
    )

    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert len(token_info.custom_fees) == 1, "Expected one royalty fee"
    retrieved_fee = token_info.custom_fees[0]

    assert isinstance(retrieved_fee, CustomRoyaltyFee), "Expected CustomRoyaltyFee instance"
    assert retrieved_fee.numerator == numerator
    assert retrieved_fee.denominator == denominator
    assert retrieved_fee.fee_collector_account_id == collector_account.id

    retrieved_fallback = retrieved_fee.fallback_fee
    assert isinstance(retrieved_fallback, CustomFixedFee), "Fallback fee should be CustomFixedFee"
    assert retrieved_fallback.amount == 5
    assert retrieved_fallback.denominated_token_id == denominated_token_id
