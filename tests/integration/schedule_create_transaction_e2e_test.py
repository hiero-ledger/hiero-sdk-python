"""
Integration tests for ScheduleCreateTransaction.
"""

import datetime

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import create_fungible_token, env


@pytest.mark.integration
def test_integration_schedule_create_transaction_can_execute(env):
    """Test that ScheduleCreateTransaction can execute."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    current_time = datetime.datetime.now()
    future_expiration = Timestamp.from_date(current_time + datetime.timedelta(seconds=30))

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule create transaction")
        .set_expiration_time(future_expiration)
        .set_wait_for_expiry(True)
        .freeze_with(env.client)
        .sign(account.key)  # Sign with the account key to pay for the transaction
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    schedule_info = (
        ScheduleInfoQuery().set_schedule_id(receipt.schedule_id).execute(env.client)
    )
    assert schedule_info is not None
    assert schedule_info.schedule_id == receipt.schedule_id
    assert schedule_info.creator_account_id == env.operator_id
    assert schedule_info.payer_account_id == account.id
    assert schedule_info.schedule_memo == "test schedule create transaction"
    assert schedule_info.expiration_time.seconds == future_expiration.seconds
    assert schedule_info.wait_for_expiry is True
    assert schedule_info.scheduled_transaction_id == receipt.scheduled_transaction_id
    assert schedule_info.scheduled_transaction_body == schedule_create_tx.schedulable_body
    assert len(schedule_info.signers) == 1
    assert (
        schedule_info.signers[0].to_bytes_raw() == account.key.public_key().to_bytes_raw()
    )


@pytest.mark.integration
def test_integration_schedule_create_transaction_can_execute_without_waiting(env):
    """Test that ScheduleCreateTransaction can execute without waiting for expiry."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    current_time = datetime.datetime.now()
    future_expiration = Timestamp.from_date(current_time + datetime.timedelta(seconds=30))

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule create transaction")
        .set_expiration_time(future_expiration)
        .freeze_with(env.client)
        .sign(account.key)  # Sign with the account key to pay for the transaction
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    schedule_info = (
        ScheduleInfoQuery().set_schedule_id(receipt.schedule_id).execute(env.client)
    )
    assert schedule_info is not None
    assert schedule_info.schedule_id == receipt.schedule_id
    assert schedule_info.creator_account_id == env.operator_id
    assert schedule_info.payer_account_id == account.id
    assert schedule_info.schedule_memo == "test schedule create transaction"
    assert schedule_info.expiration_time.seconds == future_expiration.seconds
    assert schedule_info.wait_for_expiry is False
    assert schedule_info.scheduled_transaction_id == receipt.scheduled_transaction_id
    assert schedule_info.scheduled_transaction_body == schedule_create_tx.schedulable_body
    assert schedule_info.executed_at is not None


@pytest.mark.integration
def test_integration_schedule_create_transaction_with_transfer_transaction(env):
    """Test that ScheduleCreateTransaction can schedule a transfer transaction."""
    account = env.create_account()

    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(1).to_tinybars())
        .schedule()
    )

    receipt = (
        transfer_tx.freeze_with(env.client)
        .sign(account.key)  # Sign with the sender's key as we send from the account id
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    account_info = AccountInfoQuery().set_account_id(account.id).execute(env.client)
    assert account_info.balance.to_tinybars() == 0


@pytest.mark.integration
def test_integration_schedule_create_transaction_with_consensus_submit(env):
    """Test that ScheduleCreateTransaction can schedule a ConsensusSubmitMessage transaction."""
    topic_receipt = (
        TopicCreateTransaction().set_memo("test topic for schedule").execute(env.client)
    )
    assert topic_receipt.status == ResponseCode.SUCCESS
    topic_id = topic_receipt.topic_id

    scheduled_tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message("scheduled message")
        .schedule()
    )

    receipt = (
        scheduled_tx.freeze_with(env.client).sign(env.operator_key).execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    # Confirm the message was submitted
    topic_info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert topic_info.sequence_number == 1


@pytest.mark.integration
def test_integration_schedule_create_transaction_with_token_burn(env):
    """Test that ScheduleCreateTransaction can schedule a TokenBurnTransaction."""
    initial_supply = 1000
    amount_to_burn = 500

    # Create a fungible token
    token_id = create_fungible_token(
        env, opts=[lambda tx: tx.set_initial_supply(initial_supply)]
    )

    scheduled_tx = (
        TokenBurnTransaction()
        .set_token_id(token_id)
        .set_amount(amount_to_burn)
        .schedule()
    )

    receipt = scheduled_tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    # Confirm the supply was reduced
    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
    assert token_info.total_supply == initial_supply - amount_to_burn


@pytest.mark.integration
def test_integration_schedule_create_transaction_with_token_mint(env):
    """Test that ScheduleCreateTransaction can schedule a TokenMintTransaction."""
    initial_supply = 1000
    amount_to_mint = 250

    # Create a fungible token
    token_id = create_fungible_token(
        env, opts=[lambda tx: tx.set_initial_supply(initial_supply)]
    )

    scheduled_tx = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_amount(amount_to_mint)
        .schedule()
    )

    receipt = scheduled_tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None

    # Confirm the supply was increased
    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
    assert token_info.total_supply == initial_supply + amount_to_mint


@pytest.mark.integration
def test_integration_schedule_create_transaction_invalid_expiry(env):
    """Test that ScheduleCreateTransaction fails when expiration_time is set far in the future."""
    account = env.create_account()

    # Create a simple transfer transaction
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(1).to_tinybars())
    )

    scheduled_tx = transfer_tx.schedule()

    # Set expiration time far in the future
    future_expiration = Timestamp.from_date(
        datetime.datetime.now() + datetime.timedelta(days=366)
    )

    receipt = scheduled_tx.set_expiration_time(future_expiration).execute(env.client)
    assert receipt.status == ResponseCode.SCHEDULE_EXPIRATION_TIME_TOO_FAR_IN_FUTURE, (
        f"Schedule create should have failed with status "
        f"SCHEDULE_EXPIRATION_TIME_TOO_FAR_IN_FUTURE, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_schedule_create_transaction_invalid_expiry_in_the_past(env):
    """Test that ScheduleCreateTransaction fails when expiration_time is set in the past."""
    account = env.create_account()

    # Create a simple transfer transaction
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(1).to_tinybars())
    )

    scheduled_tx = transfer_tx.schedule()

    # Set expiration time in the past
    past_time = Timestamp.from_date(
        datetime.datetime.now() - datetime.timedelta(days=366)
    )

    receipt = scheduled_tx.set_expiration_time(past_time).execute(env.client)
    assert (
        receipt.status
        == ResponseCode.SCHEDULE_EXPIRATION_TIME_MUST_BE_HIGHER_THAN_CONSENSUS_TIME
    ), (
        f"Schedule create should have failed with status "
        f"SCHEDULE_EXPIRATION_TIME_MUST_BE_HIGHER_THAN_CONSENSUS_TIME, "
        f"but got {ResponseCode(receipt.status).name}"
    )
