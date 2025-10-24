"""
Integration tests for ScheduleDeleteTransaction.
"""

import datetime

import pytest

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_delete_transaction import (
    ScheduleDeleteTransaction,
)
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_schedule_delete_transaction_can_execute(env):
    """Test that ScheduleDeleteTransaction can execute."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    current_time = datetime.datetime.now()
    future_expiration = Timestamp.from_date(
        current_time + datetime.timedelta(seconds=30)
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_admin_key(env.operator_key.public_key())
        .set_schedule_memo("test schedule delete transaction")
        .set_expiration_time(future_expiration)
        .set_wait_for_expiry(True)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None, "Schedule Info should not be None"
    assert schedule_info.deleted_at is not None, "Schedule should be deleted"


@pytest.mark.integration
def test_integration_schedule_delete_transaction_fails_with_invalid_schedule_id(env):
    """Test that ScheduleDeleteTransaction fails if schedule_id is invalid."""
    schedule_id = ScheduleId(0, 0, 999999999)
    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.INVALID_SCHEDULE_ID
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"


@pytest.mark.integration
def test_integration_schedule_delete_transaction_fails_with_invalid_signature(env):
    """Test that ScheduleDeleteTransaction fails if no signature is provided."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    current_time = datetime.datetime.now()
    future_expiration = Timestamp.from_date(
        current_time + datetime.timedelta(seconds=30)
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(env.operator_id)
        .set_admin_key(account.key.public_key())
        .set_schedule_memo("test schedule delete transaction")
        .set_expiration_time(future_expiration)
        .set_wait_for_expiry(True)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.INVALID_SIGNATURE
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None, "Schedule Info should not be None"
    assert schedule_info.deleted_at is None, "Schedule should not be deleted"


def test_integration_schedule_delete_transaction_fails_with_immutable_schedule(env):
    """Test that ScheduleDeleteTransaction fails if schedule is immutable."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    # Don't add admin key to make the schedule immutable
    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule delete transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SCHEDULE_IS_IMMUTABLE
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None, "Schedule Info should not be None"
    assert schedule_info.deleted_at is None, "Schedule should not be deleted"


def test_integration_schedule_delete_transaction_fails_schedule_already_executed(env):
    """Test that ScheduleDeleteTransaction fails if schedule is already executed."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_admin_key(env.operator_key.public_key())
        .set_schedule_memo("test schedule delete transaction")
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SCHEDULE_ALREADY_EXECUTED
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None, "Schedule Info should not be None"
    assert schedule_info.deleted_at is None, "Schedule should not be deleted"


def test_integration_schedule_delete_transaction_fails_schedule_already_deleted(env):
    """Test that ScheduleDeleteTransaction fails if schedule is already deleted."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_admin_key(env.operator_key.public_key())
        .set_schedule_memo("test schedule delete transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None, "Schedule Info should not be None"
    assert schedule_info.deleted_at is not None, "Schedule should be deleted"

    receipt = (
        ScheduleDeleteTransaction().set_schedule_id(schedule_id).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SCHEDULE_ALREADY_DELETED
    ), f"Schedule delete transaction failed with status: {ResponseCode(receipt.status).name}"
