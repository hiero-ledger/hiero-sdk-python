"""
Integration tests for revenue generating topics.
"""

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from tests.integration.utils_for_test import create_fungible_token, env

TOPIC_MEMO = "Python SDK revenue generating topic"
MESSAGE = "test_message"


def _create_custom_fee(env, token_id, amount):
    """Create a custom fee for a token."""
    return (
        CustomFixedFee()
        .set_amount_in_tinybars(amount)
        .set_denominating_token_id(token_id)
        .set_fee_collector_account_id(env.operator_id)
    )


def _create_topic(env, exempt_key1, exempt_key2, custom_fee1, custom_fee2):
    """Create a revenue generating topic with fee schedule key, exempt keys and custom fees."""
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_fee_exempt_keys([exempt_key1.public_key(), exempt_key2.public_key()])
        .set_custom_fees([custom_fee1, custom_fee2])
        .set_memo(TOPIC_MEMO)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    return topic_id


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_create(env):
    """Test that revenue generating topics can be created with custom fees."""
    # Generate exempt keys
    exempt_key1 = PrivateKey.generate_ed25519()
    exempt_key2 = PrivateKey.generate_ed25519()

    # Create custom fee tokens
    custom_fee_token_id1 = create_fungible_token(env)
    custom_fee_token_id2 = create_fungible_token(env)

    # Create custom fees
    custom_fee1 = _create_custom_fee(env, custom_fee_token_id1, 1)
    custom_fee2 = _create_custom_fee(env, custom_fee_token_id2, 2)

    topic_id = _create_topic(env, exempt_key1, exempt_key2, custom_fee1, custom_fee2)

    # Query topic info to validate everything is set
    topic_info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert topic_info is not None

    # Validate everything is set correctly
    assert topic_info.memo == TOPIC_MEMO
    assert topic_info.sequence_number == 0
    assert topic_info.admin_key is not None
    assert topic_info.fee_schedule_key is not None
    assert len(topic_info.fee_exempt_keys) == 2
    assert len(topic_info.custom_fees) == 2

    # Validate exempt keys
    exempt_key1_bytes = exempt_key1.public_key().to_bytes_raw()
    exempt_key2_bytes = exempt_key2.public_key().to_bytes_raw()
    topic_exempt_key1 = topic_info.fee_exempt_keys[0].to_bytes_raw()
    topic_exempt_key2 = topic_info.fee_exempt_keys[1].to_bytes_raw()

    assert exempt_key1_bytes == topic_exempt_key1
    assert exempt_key2_bytes == topic_exempt_key2

    # Validate custom fees
    assert topic_info.custom_fees[0].amount == custom_fee1.amount
    assert topic_info.custom_fees[1].amount == custom_fee2.amount


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_update(env):
    """Test that revenue generating topics can be updated with custom fees."""
    # Generate exempt keys
    exempt_key1 = PrivateKey.generate_ed25519()
    exempt_key2 = PrivateKey.generate_ed25519()

    # Create custom fee tokens
    custom_fee_token_id1 = create_fungible_token(env)
    custom_fee_token_id2 = create_fungible_token(env)

    # Create custom fees
    custom_fee1 = _create_custom_fee(env, custom_fee_token_id1, 1)
    custom_fee2 = _create_custom_fee(env, custom_fee_token_id2, 2)

    topic_id = _create_topic(env, exempt_key1, exempt_key2, custom_fee1, custom_fee2)

    # Generate new fee schedule key for update
    new_fee_schedule_key = PrivateKey.generate_ed25519()

    # Update the revenue generating topic with new fee schedule key, exempt key and custom fee
    receipt = (
        TopicUpdateTransaction(topic_id=topic_id)
        .set_fee_schedule_key(new_fee_schedule_key.public_key())
        .set_fee_exempt_keys([exempt_key2.public_key()])
        .set_custom_fees([custom_fee2])
        .set_memo(TOPIC_MEMO)  # Explicitly preserve the memo
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic update failed with status: {ResponseCode(receipt.status).name}"

    # Query topic info again to validate updates
    updated_topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    assert updated_topic_info is not None

    # Validate everything is updated correctly
    assert updated_topic_info.memo == TOPIC_MEMO
    assert updated_topic_info.sequence_number == 0
    assert updated_topic_info.admin_key is not None

    # Validate new fee schedule key
    new_fee_schedule_key_bytes = new_fee_schedule_key.public_key().to_bytes_raw()
    updated_fee_schedule_key = updated_topic_info.fee_schedule_key.to_bytes_raw()
    assert new_fee_schedule_key_bytes == updated_fee_schedule_key

    # Validate updated exempt keys (should only have exempt_key2)
    assert len(updated_topic_info.fee_exempt_keys) == 1
    updated_exempt_key = updated_topic_info.fee_exempt_keys[0].to_bytes_raw()
    exempt_key2_bytes = exempt_key2.public_key().to_bytes_raw()
    assert exempt_key2_bytes == updated_exempt_key

    # Validate updated custom fees (should only have custom_fee2)
    assert len(updated_topic_info.custom_fees) == 1
    assert updated_topic_info.custom_fees[0].amount == custom_fee2.amount


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_create_with_invalid_exempt_key(
    env,
):
    """Test that revenue generating topics cannot be created with invalid exempt keys."""
    exempt_key1 = PrivateKey.generate_ed25519()

    # Duplicate exempt key - should fail with FEE_EXEMPT_KEY_LIST_CONTAINS_DUPLICATED_KEY
    topic_create_transaction = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_exempt_keys([exempt_key1.public_key(), exempt_key1.public_key()])
    )

    with pytest.raises(
        PrecheckError,
        match="failed precheck with status: FEE_EXEMPT_KEY_LIST_CONTAINS_DUPLICATED_KEYS",
    ):
        topic_create_transaction.execute(env.client)

    # Generate 10 additional keys (total 11 keys, limit is 10)
    exempt_keys = []
    for _ in range(10):
        key = PrivateKey.generate_ed25519()
        exempt_keys.append(key.public_key())

    exempt_keys.append(exempt_key1.public_key())

    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_exempt_keys(exempt_keys)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.MAX_ENTRIES_FOR_FEE_EXEMPT_KEY_LIST_EXCEEDED, (
        f"Topic create should have failed with "
        f"MAX_ENTRIES_FOR_FEE_EXEMPT_KEY_LIST_EXCEEDED status but got:"
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_update_fee_schedule_key(env):
    """Test that revenue generating topics cannot update fee schedule key."""
    # Create a revenue generating topic without fee schedule key
    receipt = TopicCreateTransaction().set_admin_key(env.public_operator_key).execute(env.client)

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    # Generate new fee schedule key for update
    new_fee_schedule_key = PrivateKey.generate_ed25519()

    # Update the revenue generating topic with new fee schedule key - should fail
    receipt = (
        TopicUpdateTransaction()
        .set_topic_id(topic_id)
        .set_fee_schedule_key(new_fee_schedule_key.public_key())
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.FEE_SCHEDULE_KEY_CANNOT_BE_UPDATED, (
        f"Topic update should have failed with "
        f"FEE_SCHEDULE_KEY_CANNOT_BE_UPDATED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_update_custom_fees(env):
    """Test that revenue generating topics cannot update custom fees without fee schedule key."""
    # Create a revenue generating topic without fee schedule key
    receipt = TopicCreateTransaction().set_admin_key(env.public_operator_key).execute(env.client)

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    # Create custom fee tokens
    custom_fee_token_id1 = create_fungible_token(env)
    custom_fee_token_id2 = create_fungible_token(env)

    # Create custom fees
    custom_fee1 = _create_custom_fee(env, custom_fee_token_id1, 1)

    custom_fee2 = _create_custom_fee(env, custom_fee_token_id2, 2)

    # Update the revenue generating topic with new custom fees - should fail
    receipt = (
        TopicUpdateTransaction(topic_id=topic_id)
        .set_custom_fees([custom_fee1, custom_fee2])
        .set_fee_schedule_key(env.public_operator_key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.FEE_SCHEDULE_KEY_NOT_SET, (
        f"Topic update should have failed with FEE_SCHEDULE_KEY_NOT_SET"
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_charge_hbars_with_limit(env):
    """Test that revenue generating topics can charge HBARs with custom fee limit."""
    hbar_amount = 100_000_000  # 1 HBAR in tinybars
    custom_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar.from_tinybars(hbar_amount // 2))  # 0.5 HBAR fee
        .set_fee_collector_account_id(env.operator_id)
    )

    # Create a revenue generating topic with HBAR custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_memo(TOPIC_MEMO)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)  # 1 HBAR balance

    # Create custom fee limit
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(CustomFixedFee().set_hbar_amount(Hbar.from_tinybars(hbar_amount)))
    )

    # Set operator to payer
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    # Reset operator to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee charged
    account_info = AccountInfoQuery().set_account_id(payer_account.id).execute(env.client)
    assert account_info.balance.to_tinybars() < hbar_amount // 2


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_charge_hbars_without_limit(env):
    """Test that revenue generating topics can charge HBARs without custom fee limit."""
    hbar_amount = 100_000_000  # 1 HBAR in tinybars
    custom_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar.from_tinybars(hbar_amount // 2))  # 0.5 HBAR fee
        .set_fee_collector_account_id(env.operator_id)
    )

    # Create a revenue generating topic with HBAR custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)  # 1 HBAR balance

    # Submit a message to the revenue generating topic without custom fee limit
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction().set_message(MESSAGE).set_topic_id(topic_id)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    # Reset operator to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee charged
    account_info = AccountInfoQuery().set_account_id(payer_account.id).execute(env.client)
    assert account_info.balance.to_tinybars() < hbar_amount // 2


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_charge_tokens_with_limit(env):
    """Test that revenue generating topics can charge tokens with custom fee limit."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 1)

    # Create a revenue generating topic with token custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    env.associate_and_transfer(payer_account.id, payer_account.key, token_id, 1)

    # Create custom fee limit
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_amount_in_tinybars(2).set_denominating_token_id(token_id)
        )
    )

    # Set operator to payer
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    # Reset operator to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee charged
    account_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(payer_account.id).execute(env.client)
    )
    assert account_balance.token_balances.get(token_id) == 0


@pytest.mark.integration
def test_integration_revenue_generating_topic_can_charge_tokens_without_limit(env):
    """Test that revenue generating topics can charge tokens without custom fee limit."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 1)

    # Create a revenue generating topic
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    env.associate_and_transfer(payer_account.id, payer_account.key, token_id, 1)

    # Set operator to payer
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction().set_message(MESSAGE).set_topic_id(topic_id)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    # Reset operator to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee charged
    account_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(payer_account.id).execute(env.client)
    )
    assert account_balance.token_balances.get(token_id) == 0


@pytest.mark.integration
def test_integration_revenue_generating_topic_does_not_charge_hbars_fee_exempt_keys(env):
    """Test that revenue generating topics do not charge HBARs for fee exempt keys."""
    hbar_amount = 100_000_000  # 1 HBAR in tinybars
    custom_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar.from_tinybars(hbar_amount // 2))  # 0.5 HBAR fee
        .set_fee_collector_account_id(env.operator_id)
    )

    fee_exempt_key1 = PrivateKey.generate_ed25519()
    fee_exempt_key2 = PrivateKey.generate_ed25519()

    # Create a revenue generating topic with HBAR custom fee and 2 fee exempt keys
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_fee_exempt_keys([fee_exempt_key1.public_key(), fee_exempt_key2.public_key()])
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    # Create payer with 1 HBAR and fee exempt key
    receipt = (
        AccountCreateTransaction()
        .set_key(fee_exempt_key1.public_key())
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"
    payer_account = receipt.account_id
    assert payer_account is not None

    # Submit a message to the revenue generating topic without custom fee limit
    env.client.set_operator(payer_account, fee_exempt_key1)

    message_transaction = (
        TopicMessageSubmitTransaction().set_message(MESSAGE).set_topic_id(topic_id)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    # Reset operator to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee is not charged
    account_info = AccountInfoQuery().set_account_id(payer_account).execute(env.client)
    assert account_info.balance.to_tinybars() > hbar_amount // 2


@pytest.mark.integration
def test_integration_revenue_generating_topic_does_not_charge_tokens_fee_exempt_keys(
    env,
):
    """Test that revenue generating topics do not charge tokens for fee exempt keys."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 1)

    fee_exempt_key1 = PrivateKey.generate_ed25519()
    fee_exempt_key2 = PrivateKey.generate_ed25519()

    # Create a revenue generating topic with token custom fee and 2 fee exempt keys
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_fee_exempt_keys([fee_exempt_key1.public_key(), fee_exempt_key2.public_key()])
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    receipt = (
        AccountCreateTransaction()
        .set_key(fee_exempt_key1.public_key())
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"
    payer_account = receipt.account_id
    assert payer_account is not None

    env.associate_and_transfer(payer_account, fee_exempt_key1, token_id, 1)

    env.client.set_operator(payer_account, fee_exempt_key1)

    message_transaction = (
        TopicMessageSubmitTransaction().set_message(MESSAGE).set_topic_id(topic_id)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    env.client.set_operator(env.operator_id, env.operator_key)

    # Verify the custom fee is not charged
    account_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(payer_account).execute(env.client)
    )
    assert account_balance.token_balances.get(token_id) == 1


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_charge_hbars_with_lower_limit(env):
    """Test that revenue generating topics cannot charge HBARs with lower custom fee limit."""
    hbar_amount = 100_000_000  # 1 HBAR in tinybars
    custom_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar.from_tinybars(hbar_amount // 2))  # 0.5 HBAR fee
        .set_fee_collector_account_id(env.operator_id)
    )

    # Create a revenue generating topic with HBAR custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    # Create custom fee limit with lower amount than the custom fee
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_hbar_amount(Hbar.from_tinybars((hbar_amount // 2) - 1))
        )
    )

    # Submit a message to the revenue generating topic with custom fee limit
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert message_receipt.status == ResponseCode.MAX_CUSTOM_FEE_LIMIT_EXCEEDED, (
        f"Message submit should have failed with MAX_CUSTOM_FEE_LIMIT_EXCEEDED status but got: "
        f"{ResponseCode(message_receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_charge_tokens_with_lower_limit(
    env,
):
    """Test that revenue generating topics cannot charge tokens with lower custom fee limit."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 2)

    # Create a revenue generating topic with token custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    env.associate_and_transfer(payer_account.id, payer_account.key, token_id, 2)

    # Create custom fee limit with lower amount than the custom fee
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_amount_in_tinybars(1).set_denominating_token_id(token_id)
        )
    )

    # Submit a message to the revenue generating topic with custom fee limit
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert message_receipt.status == ResponseCode.MAX_CUSTOM_FEE_LIMIT_EXCEEDED, (
        f"Message submit should have failed with MAX_CUSTOM_FEE_LIMIT_EXCEEDED status but got: "
        f"{ResponseCode(message_receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_scheduled_revenue_topic_cannot_charge_hbars_with_lower_limit(env):
    """Test that scheduled revenue topics cannot charge HBARs with lower custom fee limit."""
    hbar_amount = 100_000_000  # 1 HBAR in tinybars
    custom_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar.from_tinybars(hbar_amount // 2))  # 0.5 HBAR fee
        .set_fee_collector_account_id(env.operator_id)
    )

    # Create a revenue generating topic with HBAR custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    # Create custom fee limit with lower amount than the custom fee
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_hbar_amount(Hbar.from_tinybars((hbar_amount // 2) - 1))
        )
    )

    env.client.set_operator(payer_account.id, payer_account.key)  # Set operator to payer

    # Submit a message to the revenue generating topic with custom fee limit
    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
        .schedule()
    )
    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submit failed with status: {ResponseCode(message_receipt.status).name}"

    env.client.set_operator(env.operator_id, env.operator_key)  # Reset operator to original

    # Verify the custom fee did not charge
    account_info = AccountInfoQuery().set_account_id(payer_account.id).execute(env.client)

    assert account_info.balance.to_tinybars() > hbar_amount // 2, (
        f"Expected balance to be greater than {hbar_amount // 2} tinybars, "
        f"but got {account_info.balance.to_tinybars()}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_execute_with_invalid_token_id(
    env,
):
    """Test that revenue generating topics fail with invalid token ID in custom fee limit."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 2)

    # Create a revenue generating topic with token custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    env.associate_and_transfer(payer_account.id, payer_account.key, token_id, 2)

    invalid_token_id = TokenId(0, 0, 0)

    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_amount_in_tinybars(2).set_denominating_token_id(invalid_token_id)
        )
    )

    # Set operator to payer
    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert message_receipt.status == ResponseCode.NO_VALID_MAX_CUSTOM_FEE, (
        f"Message submit should have failed with NO_VALID_MAX_CUSTOM_FEE status but got: "
        f"{ResponseCode(message_receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_revenue_generating_topic_cannot_execute_with_duplicate_denomination(
    env,
):
    """Test that topics reject duplicate token IDs in custom fee limit."""
    token_id = create_fungible_token(env)

    custom_fee = _create_custom_fee(env, token_id, 2)

    # Create a revenue generating topic with token custom fee
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"

    topic_id = receipt.topic_id
    assert topic_id is not None

    payer_account = env.create_account(1)

    env.associate_and_transfer(payer_account.id, payer_account.key, token_id, 2)

    # Set custom fee limit with duplicate denomination token ID
    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(payer_account.id)
        .add_custom_fee(
            CustomFixedFee().set_amount_in_tinybars(1).set_denominating_token_id(token_id)
        )
        .add_custom_fee(
            CustomFixedFee().set_amount_in_tinybars(2).set_denominating_token_id(token_id)
        )
    )

    # Set operator to payer
    env.client.set_operator(payer_account.id, payer_account.key)

    # Submit a message to the revenue generating topic
    message_transaction = (
        TopicMessageSubmitTransaction()
        .set_message(MESSAGE)
        .set_topic_id(topic_id)
        .add_custom_fee_limit(custom_fee_limit)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()

    # Submit message should fail
    with pytest.raises(
        PrecheckError,
        match="failed precheck with status: DUPLICATE_DENOMINATION_IN_MAX_CUSTOM_FEE_LIST",
    ):
        message_transaction.execute(env.client)


@pytest.mark.integration
def test_integration_revenue_generating_topic_does_not_charge_treasuries(env):
    """Test that revenue generating topics do not charge treasuries."""
    payer_account = env.create_account(1)

    token_id = create_fungible_token(
        env,
        [
            lambda tx: tx.set_treasury_account_id(payer_account.id),
            lambda tx: tx.set_initial_supply(1),
            lambda tx: tx.freeze_with(env.client).sign(payer_account.key),
        ],
    )

    receipt = (
        TokenAssociateTransaction()
        .set_account_id(env.operator_id)
        .add_token_id(token_id)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token association failed with status: {ResponseCode(receipt.status).name}"

    custom_fee = _create_custom_fee(env, token_id, 1)

    receipt = (
        TopicCreateTransaction()
        .set_admin_key(env.public_operator_key)
        .set_fee_schedule_key(env.public_operator_key)
        .set_custom_fees([custom_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
    topic_id = receipt.topic_id
    assert topic_id is not None

    env.client.set_operator(payer_account.id, payer_account.key)

    message_transaction = (
        TopicMessageSubmitTransaction().set_message(MESSAGE).set_topic_id(topic_id)
    )

    message_transaction.transaction_fee = Hbar(2).to_tinybars()
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    env.client.set_operator(env.operator_id, env.operator_key)

    account_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(payer_account.id).execute(env.client)
    )
    assert account_balance.token_balances.get(token_id) == 1
