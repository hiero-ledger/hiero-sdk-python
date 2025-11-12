import pytest

from hiero_sdk_python.hbar import Hbar
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token 
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction

@pytest.mark.integration
def test_token_fee_schedule_update_e2e_fungible():
    """Test updating fee schedule successfully for a Fungible Token."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = env.operator_key
        token_id = create_fungible_token(
            env,
            opts=[lambda tx: tx.set_fee_schedule_key(fee_schedule_key)]
        )
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
            f"Fee schedule update failed: {ResponseCode(update_receipt.status).name}"

        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert token_info.custom_fees and len(token_info.custom_fees) == 1
        retrieved_fee = token_info.custom_fees[0]
        assert isinstance(retrieved_fee, CustomFixedFee) and retrieved_fee.amount == 25
    finally:
        env.close()

@pytest.mark.integration
def test_token_fee_schedule_update_e2e_nft():
    """Test updating fee schedule successfully for an NFT."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = env.operator_key
        token_id = create_nft_token(
            env,
            opts=[lambda tx: tx.set_fee_schedule_key(fee_schedule_key)]
        )
        assert token_id is not None

        new_fee = CustomRoyaltyFee(
            numerator=1,
            denominator=10, # 10% royalty
            fee_collector_account_id=env.operator_id,
        )
        update_tx = TokenFeeScheduleUpdateTransaction()
        update_tx.set_token_id(token_id)
        update_tx.set_custom_fees([new_fee])
        update_tx.freeze_with(env.client)
        update_tx.sign(fee_schedule_key)
        update_receipt = update_tx.execute(env.client)

        assert update_receipt.status == ResponseCode.SUCCESS, \
            f"Fee schedule update failed: {ResponseCode(update_receipt.status).name}"

        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert token_info.custom_fees and len(token_info.custom_fees) == 1
        assert isinstance(token_info.custom_fees[0], CustomRoyaltyFee)
    finally:
        env.close()

@pytest.mark.integration
def test_token_fee_schedule_update_fails_with_invalid_signature():
    """Test failure with an incorrect signature."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = PrivateKey.generate() # Must be a new key
        token_id = create_fungible_token(
            env,
            opts=[lambda tx: tx.set_fee_schedule_key(fee_schedule_key)]
        )
        assert token_id is not None

        wrong_key = PrivateKey.generate()
        new_fee = CustomFixedFee(amount=50, fee_collector_account_id=env.operator_id)
        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.freeze_with(env.client)
        update_tx.sign(wrong_key) # Sign with the wrong key

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
def test_token_fee_schedule_update_fails_for_deleted_token():
    """Test failure when attempting to update a deleted token."""
    env = IntegrationTestEnv()
    try:
        admin_key = env.operator_key
        fee_schedule_key = env.operator_key
        token_id = create_fungible_token(
            env,
            opts=[
                lambda tx: tx.set_admin_key(admin_key),
                lambda tx: tx.set_fee_schedule_key(fee_schedule_key)
            ]
        )
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

@pytest.mark.integration
def test_token_fee_schedule_update_fails_royalty_on_fungible():
    """Test failure when adding a royalty fee to a fungible token."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = env.operator_key
        token_id = create_fungible_token(
            env,
            opts=[lambda tx: tx.set_fee_schedule_key(fee_schedule_key)]
        )
        assert token_id is not None

        new_fee = CustomRoyaltyFee(numerator=1, denominator=10, fee_collector_account_id=env.operator_id)
        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.freeze_with(env.client).sign(fee_schedule_key)
        update_receipt = update_tx.execute(env.client)
        
        assert update_receipt.status == ResponseCode.CUSTOM_ROYALTY_FEE_ONLY_ALLOWED_FOR_NON_FUNGIBLE_UNIQUE, \
            f"Expected CUSTOM_ROYALTY_FEE_ONLY_ALLOWED_FOR_NON_FUNGIBLE_UNIQUE, but got {ResponseCode(update_receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_fee_schedule_update_fails_fractional_on_nft():
    """Test failure when adding a fractional fee to an NFT."""
    env = IntegrationTestEnv()
    try:
        fee_schedule_key = env.operator_key
        token_id = create_nft_token(
            env,
            opts=[lambda tx: tx.set_fee_schedule_key(fee_schedule_key)]
        )
        assert token_id is not None

        new_fee = CustomFractionalFee(
            numerator=1, 
            denominator=100, 
            min_amount=1, 
            max_amount=10, 
            fee_collector_account_id=env.operator_id
        )
        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([new_fee])
        )
        update_tx.freeze_with(env.client).sign(fee_schedule_key)
        update_receipt = update_tx.execute(env.client)
        
        assert update_receipt.status == ResponseCode.CUSTOM_FRACTIONAL_FEE_ONLY_ALLOWED_FOR_FUNGIBLE_COMMON, \
            f"Expected CUSTOM_FRACTIONAL_FEE_ONLY_ALLOWED_FOR_FUNGIBLE_COMMON, but got {ResponseCode(update_receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_fee_schedule_update_clears_fees():
    """Test successfully clearing all fees by passing an empty list."""
    env = IntegrationTestEnv()
    try:
        admin_key = env.operator_key
        fee_schedule_key = env.operator_key
        
        initial_fee = CustomFixedFee(amount=10, fee_collector_account_id=env.operator_id)
        token_id = create_fungible_token(
            env,
            opts=[
                lambda tx: tx.set_custom_fees([initial_fee]),
                lambda tx: tx.set_admin_key(admin_key),
                lambda tx: tx.set_fee_schedule_key(fee_schedule_key)
            ]
        )
        assert token_id is not None
        
        token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert len(token_info.custom_fees) == 1

        update_tx = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([]) # Pass empty list
        )
        update_tx.freeze_with(env.client).sign(fee_schedule_key)
        update_receipt = update_tx.execute(env.client)
        
        assert update_receipt.status == ResponseCode.SUCCESS, \
            f"Fee schedule update (clear) failed: {ResponseCode(update_receipt.status).name}"

        token_info_cleared = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        assert len(token_info_cleared.custom_fees) == 0
    finally:
        env.close()
