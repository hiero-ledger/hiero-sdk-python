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
def test_token_fee_schedule_update_e2e_fails_due_to_missing_key():
    env = IntegrationTestEnv()
    try:
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
            supply_key=env.operator_key,
        )

        create_tx = TokenCreateTransaction(token_params=token_params, keys=keys)
        create_tx.transaction_fee = Hbar(30).to_tinybars()
        create_receipt = create_tx.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Token creation failed: {ResponseCode(create_receipt.status).name}"
        token_id = create_receipt.token_id
        assert token_id is not None

        new_fee = CustomFixedFee(
            amount=25,
            fee_collector_account_id=env.operator_id,
        )
        new_fee_list = [new_fee]

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees(new_fee_list)
        )
        update_tx.transaction_fee = Hbar(5).to_tinybars()
        update_tx.freeze_with(env.client)
        update_tx.sign(admin_key)

        update_receipt = update_tx.execute(env.client)

        assert update_receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY, \
            f"Expected TOKEN_HAS_NO_FEE_SCHEDULE_KEY, but got {ResponseCode(update_receipt.status).name}"

    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_due_to_missing_key_before_sig_check():
    env = IntegrationTestEnv()
    try:
        admin_key = env.operator_key

        token_params = TokenParams(
            token_name="Invalid Sig Test",
            token_symbol="SIG",
            treasury_account_id=env.operator_id,
            initial_supply=100,
        )
        keys = TokenKeys(admin_key=admin_key)

        create_receipt = TokenCreateTransaction(token_params=token_params, keys=keys).execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, "Token creation failed"
        token_id = create_receipt.token_id
        assert token_id is not None

        wrong_key = PrivateKey.generate()
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.transaction_fee = Hbar(5).to_tinybars()
        update_tx.freeze_with(env.client)
        update_tx.sign(wrong_key)

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY, (
            f"Expected TOKEN_HAS_NO_FEE_SCHEDULE_KEY, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_with_invalid_token_id():
    env = IntegrationTestEnv()
    try:
        invalid_token_id = TokenId(0, 0, 9999999)
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(invalid_token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.transaction_fee = Hbar(5).to_tinybars()

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.INVALID_TOKEN_ID, (
            f"Expected INVALID_TOKEN_ID, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_token_fee_schedule_update_fails_precheck_without_token_id():
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
        update_tx.transaction_fee = Hbar(5).to_tinybars()

        update_receipt = update_tx.execute(env.client)
        assert update_receipt.status == ResponseCode.TOKEN_WAS_DELETED, (
            f"Expected TOKEN_WAS_DELETED, but got {ResponseCode(update_receipt.status).name}"
        )
    finally:
        env.close()
