"""
Integration tests for the TopicMessageSubmitTransaction class.
"""

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from tests.integration.utils_for_test import  env

def create_topic(client, admin_key=None, submit_key=None, custom_fees=None):
    """Helper transaction for creating a topic."""
    tx = TopicCreateTransaction(memo="Python SDK topic")

    if admin_key:
        tx.set_admin_key(admin_key)
    if submit_key:
        tx.set_submit_key(submit_key)
    if custom_fees:
        tx.set_custom_fees(custom_fees)

    receipt = tx.execute(client)
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Topic creation failed: {ResponseCode(receipt.status).name}"
    )
    return receipt.topic_id


def delete_topic(client, topic_id):
    """Helper transaction to delete a topic."""
    receipt = (
        TopicDeleteTransaction(topic_id=topic_id)
        .execute(client)
    )

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_can_execute(env):
    """Test that a topic message submit transaction executes."""
    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that no message is submitted
    assert info.sequence_number == 0

    message_transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message="Hello, Python SDK!"
    )

    message_transaction.freeze_with(env.client)
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that one message is submitted
    assert info.sequence_number == 1

    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_topic_message_submit_transaction_can_submit_a_large_message(env):
    """Test topic message submit transaction can submit large message."""
    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key
    )

    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert info.sequence_number == 0

    message = "A" * (1024 * 14) # message with (1024 * 14) bytes ie 14 chunks

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

    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_topic_message_submit_transaction_fails_if_max_chunks_less_than_requied(env):
    """Test topic message submit transaction fails if max_chunks less than requied."""
    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key
    )

    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert info.sequence_number == 0

    message = "A" * (1024 * 14) # message with (1024 * 14) bytes ie 14 chunks

    message_tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message(message)
        .set_max_chunks(2)
        .freeze_with(env.client)
    )

    with pytest.raises(ValueError):
        message_receipt = message_tx.execute(env.client)
    
    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_with_submit_key(env):
    """Test that a topic message submit transaction executes with submit key."""
    submit_key = PrivateKey.generate()

    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key,
        submit_key=submit_key
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that no message is  submited
    assert info.sequence_number == 0

    message_transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message="Hello, Python SDK!"
    )

    message_transaction.freeze_with(env.client)
    # Sign with submit key
    message_transaction.sign(submit_key) 
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.SUCCESS
    ), f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that one message is  submited
    assert info.sequence_number == 1

    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_without_submit_key_fails(env):
    """Test that a topic message fails submitting transaction without submit key."""
    submit_key = PrivateKey.generate()

    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key,
        submit_key=submit_key
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that no message is  submited
    assert info.sequence_number == 0

    message_transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message="Hello, Python SDK!"
    )

    message_transaction.freeze_with(env.client)
    message_receipt = message_transaction.execute(env.client)

    assert (
        message_receipt.status == ResponseCode.INVALID_SIGNATURE
    ), f"Message submission must fail with status: {ResponseCode.INVALID_SIGNATURE}"

    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_can_execute_with_custom_fee_limit(env):
    """Test that a topic message submit transaction executes with a custom fee limit."""
    operator_id, operator_key = env.operator_id, env.operator_key

    account = env.create_account(3)  # Create an account with 3 Hbar balance

    topic_fee = (
        CustomFixedFee().set_hbar_amount(Hbar(1)).set_fee_collector_account_id(env.operator_id)
    )

    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key,
        custom_fees=[topic_fee]
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    assert info.sequence_number == 0

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

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    assert info.sequence_number == 1

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() < Hbar(2).to_tinybars()
    ), f"Expected balance of less than 2 Hbar, but got {balance.hbars.to_tinybars()}"

    env.client.set_operator(operator_id, operator_key)
    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_integration_scheduled_topic_message_submit_transaction_can_execute_with_custom_fee_limit(env):
    """Test that a scheduled topic message submit transaction executes with a custom fee limit."""
    operator_id, operator_key = env.operator_id, env.operator_key

    account = env.create_account(3)  # Create an account with 3 Hbar balance

    topic_fee = (
        CustomFixedFee().set_hbar_amount(Hbar(1)).set_fee_collector_account_id(env.operator_id)
    )

    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key,
        custom_fees=[topic_fee]
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    assert info.sequence_number == 0

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() == Hbar(3).to_tinybars()
    ), f"Expected balance of 3 Hbar, but got {balance.hbars.to_tinybars()}"

    # Restore the operator to the original account
    env.client.set_operator(account.id, account.key)

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

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    assert info.sequence_number == 1

    balance = CryptoGetAccountBalanceQuery().set_account_id(account.id).execute(env.client)
    assert (
        balance.hbars.to_tinybars() < Hbar(2).to_tinybars()
    ), f"Expected balance of less than 2 Hbar, but got {balance.hbars.to_tinybars()}"

    # Restore the operator to the original account
    env.client.set_operator(operator_id, operator_key)
    delete_topic(env.client, topic_id)


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_fails_if_required_chunk_greater_than_max_chunk(env):
    """Test that a topic message fails submitting transaction when required chunk greater than max_chunks."""
    submit_key = PrivateKey.generate()

    topic_id = create_topic(
        client=env.client,
        admin_key=env.operator_key,
        submit_key=submit_key
    )

    info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
    # Check that no message is  submited
    assert info.sequence_number == 0

    message_transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message="A"*(1024*4) # requires 4 chunks
    )
    message_transaction.set_max_chunks(2)
    message_transaction.freeze_with(env.client)
    with pytest.raises(ValueError, match="Message requires 4 chunks but max_chunks=2. Increase limit with set_max_chunks()."):
        message_transaction.execute(env.client)
    
    delete_topic(env.client, topic_id)