"""
Integration tests for the TopicMessageSubmitTransaction class.
"""

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from tests.integration.utils_for_test import  env

def get_topic_info(client, topic_id):
    return TopicInfoQuery().set_topic_id(topic_id).execute(client)


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_can_execute(env):
    """Test that a topic message submit transaction executes."""
    create_transaction = TopicCreateTransaction(
        memo="Python SDK topic", admin_key=env.public_operator_key
    )

    create_transaction.freeze_with(env.client)
    create_receipt = create_transaction.execute(env.client)
    topic_id = create_receipt.topic_id

    message_transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id, message="Hello, Python SDK!"
    )

    message_transaction.freeze_with(env.client)
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
    delete_transaction.freeze_with(env.client)
    delete_receipt = delete_transaction.execute(env.client)

    assert (
        delete_receipt.status == ResponseCode.SUCCESS
    ), f"Topic deletion failed with status: {ResponseCode(delete_receipt.status).name}"


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_can_execute_with_custom_fee_limit(env):
    """Test that a topic message submit transaction executes with a custom fee limit."""
    
    account = env.create_account(3)  # Create an account with 3 Hbar balance

    topic_fee = (
        CustomFixedFee().set_hbar_amount(Hbar(1)).set_fee_collector_account_id(env.operator_id)
    )

    receipt = (
        TopicCreateTransaction()
        .set_memo("Python SDK topic")
        .set_custom_fees([topic_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
    topic_id = receipt.topic_id

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() == Hbar(3).to_tinybars()
    ), f"Expected balance of 3 Hbar, but got {balance.hbars.to_tinybars()}"

    env.client.set_operator(account.id, account.key)  # Set the operator to the account

    topic_message_submit_fee_limit = (
        CustomFeeLimit().set_payer_id(account.id).add_custom_fee(topic_fee)
    )  # Create a custom limit for the topic message submit transaction

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message("Hello, Python SDK!")
        .add_custom_fee_limit(topic_message_submit_fee_limit)
    )

    tx.transaction_fee = Hbar(2).to_tinybars()
    receipt = tx.execute(env.client)

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(receipt.status).name}"

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() < Hbar(2).to_tinybars()
    ), f"Expected balance of less than 2 Hbar, but got {balance.hbars.to_tinybars()}"
    


@pytest.mark.integration
def test_integration_scheduled_topic_message_submit_transaction_can_execute_with_custom_fee_limit(env):
    """Test that a scheduled topic message submit transaction executes with a custom fee limit."""
    account = env.create_account(3)  # Create an account with 3 Hbar balance

    topic_fee = (
        CustomFixedFee().set_hbar_amount(Hbar(1)).set_fee_collector_account_id(env.operator_id)
    )

    receipt = (
        TopicCreateTransaction()
        .set_memo("Python SDK topic")
        .set_custom_fees([topic_fee])
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
    topic_id = receipt.topic_id

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() == Hbar(3).to_tinybars()
    ), f"Expected balance of 3 Hbar, but got {balance.hbars.to_tinybars()}"

    env.client.set_operator(account.id, account.key)  # Set the operator to the account

    topic_message_submit_fee_limit = (
        CustomFeeLimit().set_payer_id(account.id).add_custom_fee(topic_fee)
    )  # Create a custom limit for the topic message submit transaction

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message("Hello, Python SDK!")
        .add_custom_fee_limit(topic_message_submit_fee_limit)
        .schedule()
    )
    tx.transaction_fee = Hbar(2).to_tinybars()
    receipt = tx.execute(env.client)

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(receipt.status).name}"

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() < Hbar(2).to_tinybars()
    ), f"Expected balance of less than 2 Hbar, but got {balance.hbars.to_tinybars()}"


def test_topic_message_submit_transation_can_submit_a_large_message(env):
    """Test topic message submit transaction can submit large message."""
    topic_tx = (
        TopicCreateTransaction(
            memo="Python SDK topic",
            admin_key=env.operator_key
        )
        .freeze_with(env.client)
    )

    topic_receipt = topic_tx.execute(env.client)

    assert topic_receipt.status == ResponseCode.SUCCESS
    
    topic_id = topic_receipt.topic_id

    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)

    # Check no message has been submited
    assert info.sequence_number == 0

    message = "A" * (1024 * 14)

    message_tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message(message)
        .freeze_with(env.client)
    )

    message_receipt = message_tx.execute(env.client)
    
    assert message_receipt.status == ResponseCode.SUCCESS

    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert info.sequence_number == 14