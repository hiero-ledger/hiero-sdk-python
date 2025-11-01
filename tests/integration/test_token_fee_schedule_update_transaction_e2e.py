import pytest

from hiero_sdk_python.hbar import Hbar
from tests.integration.utils_for_test import IntegrationTestEnv
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction


@pytest.mark.integration
def test_token_fee_schedule_update_e2e():
    """Test updating fee schedule successfully."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = env.operator_key
        admin_key = env.operator_key

        initial_fee = CustomFixedFee(
            amount=10,
            fee_collector_account_id=env.operator_id,
        )
        token_params = TokenParams(
            token_name="Test Token E2E",
            token_symbol="TESTE2E",
            treasury_account_id=env.operator_id,
            initial_supply=1000,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
            custom_fees=[initial_fee],
        )
        keys = TokenKeys(
            admin_key=admin_key,
            supply_key=env.operator_key
        )

        create_tx = TokenCreateTransaction(token_params=token_params, keys=keys)
        create_tx.set_fee_schedule_key(fee_schedule_key)

        create_receipt = create_tx.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Token creation failed: {ResponseCode(create_receipt.status).name}"
        token_id = create_receipt.token_id
        assert token_id is not None

        new_fee = CustomFixedFee(
            amount=25,
            fee_collector_account_id=env.operator_id,
        )
        update_tx = TokenFeeScheduleUpdateTransaction()
        update_tx.set_token_id(token_id)
        update_tx.set_custom_fees([new_fee])
        update_tx.freeze_with(env.client)
        update_tx.sign(fee_schedule_key)

        update_receipt = update_tx.execute(env.client)

        assert update_receipt.status == ResponseCode.SUCCESS, \
            f"Fee schedule update failed unexpectedly: {ResponseCode(update_receipt.status).name}"

        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert token_info.custom_fees and len(token_info.custom_fees) == 1
        retrieved_fee = token_info.custom_fees[0]
        assert isinstance(retrieved_fee, CustomFixedFee) and retrieved_fee.amount == 25

    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_with_invalid_signature():
    """Test failure with an incorrect signature."""
    env = IntegrationTestEnv()
    try:
        # Admin key can be the operator
        admin_key = env.operator_key
        # Fee schedule key MUST be a new, separate key for this test
        fee_schedule_key = PrivateKey.generate()

        token_params = TokenParams(
            token_name="Invalid Sig Test",
            token_symbol="SIG",
            treasury_account_id=env.operator_id,
            initial_supply=100,
        )
        keys = TokenKeys(admin_key=admin_key)

        create_tx = TokenCreateTransaction(token_params=token_params, keys=keys)
        # Set the fee schedule key to the new key
        create_tx.set_fee_schedule_key(fee_schedule_key)

        # Create the token (signed by admin_key, which execute() handles)
        create_receipt = create_tx.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, "Token creation failed"
        token_id = create_receipt.token_id
        assert token_id is not None

        # Generate a different wrong key
        wrong_key = PrivateKey.generate()
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.freeze_with(env.client)
        update_tx.sign(wrong_key) # Sign with the wrong key

        # execute() will auto-sign with operator_key, but the
        # network requires the *fee_schedule_key*, which is missing.
        update_receipt = update_tx.execute(env.client)
        
        assert update_receipt.status == ResponseCode.INVALID_SIGNATURE, (
            f"Expected INVALID_SIGNATURE, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_with_invalid_token_id():
    """Test failure with a non-existent token ID."""
    env = IntegrationTestEnv()
    try:
        invalid_token_id = TokenId(0, 0, 9999999)
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(invalid_token_id)
            .set_custom_fees([new_fee])
        )

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.INVALID_TOKEN_ID, (
            f"Expected INVALID_TOKEN_ID, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_precheck_without_token_id():
    """Test precheck failure when token ID is missing."""
    env = IntegrationTestEnv()
    try:
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)
        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_custom_fees([new_fee])
        )

        with pytest.raises(ValueError, match="Missing token ID"):
            update_tx.execute(env.client)
    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_for_deleted_token():
    """Test failure when attempting to update a deleted token."""
    env = IntegrationTestEnv()
    try:
        admin_key = env.operator_key
        token_params = TokenParams(
            token_name="Token to be Deleted",
            token_symbol="DEL",
            treasury_account_id=env.operator_id,
            initial_supply=100,
        )
        keys = TokenKeys(admin_key=admin_key) 

        create_receipt = TokenCreateTransaction(token_params=token_params, keys=keys).execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, "Token creation failed"
        token_id = create_receipt.token_id
        assert token_id is not None

        delete_receipt = TokenDeleteTransaction().set_token_id(token_id).execute(env.client)
        assert delete_receipt.status == ResponseCode.SUCCESS, "Token deletion failed"

        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)
        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.TOKEN_WAS_DELETED, (
            f"Expected TOKEN_WAS_DELETED, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()
