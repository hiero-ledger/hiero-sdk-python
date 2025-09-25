"""
Integration tests for ScheduleInfoQuery.
"""

import datetime

import pytest

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_schedule_info_query_can_execute(env):
    """Test that ScheduleInfoQuery can execute."""
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
        .set_admin_key(env.operator_key.public_key())
        .set_schedule_memo("test schedule info query")
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

    schedule_info = (
        ScheduleInfoQuery().set_schedule_id(receipt.schedule_id).execute(env.client)
    )
    assert schedule_info is not None
    assert schedule_info.ledger_id is not None
    assert schedule_info.schedule_id == receipt.schedule_id
    assert schedule_info.creator_account_id == env.operator_id
    assert schedule_info.payer_account_id == account.id
    assert schedule_info.schedule_memo == "test schedule info query"
    assert schedule_info.expiration_time.seconds == future_expiration.seconds
    assert schedule_info.wait_for_expiry is True
    assert schedule_info.scheduled_transaction_id == receipt.scheduled_transaction_id
    assert schedule_info.scheduled_transaction_body == schedule_create_tx.schedulable_body
    assert len(schedule_info.signers) == 1
    assert (
        schedule_info.signers[0].to_bytes_raw() == account.key.public_key().to_bytes_raw()
    )
    assert (
        schedule_info.admin_key.to_bytes_raw()
        == env.operator_key.public_key().to_bytes_raw()
    )


@pytest.mark.integration
def test_integration_schedule_info_query_get_cost(env):
    """Test that ScheduleInfoQuery can calculate query costs."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule info query cost")
        .freeze_with(env.client)
        .sign(account.key)  # Sign with the account key to pay for the transaction
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None

    schedule_info = ScheduleInfoQuery().set_schedule_id(receipt.schedule_id)

    cost = schedule_info.get_cost(env.client)

    info = schedule_info.set_query_payment(cost).execute(env.client)

    assert info.schedule_id == receipt.schedule_id


@pytest.mark.integration
def test_integration_schedule_info_query_insufficient_payment(env):
    """Test that ScheduleInfoQuery fails with insufficient payment."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule info query insufficient payment")
        .freeze_with(env.client)
        .sign(account.key)  # Sign with the account key to pay for the transaction
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule create transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None

    schedule_info = ScheduleInfoQuery().set_schedule_id(receipt.schedule_id)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        schedule_info.set_query_payment(Hbar.from_tinybars(1)).execute(env.client)


@pytest.mark.integration
def test_integration_schedule_info_query_fails_with_invalid_schedule_id(env):
    """Test that the ScheduleInfoQuery fails with an invalid schedule ID."""
    # Create a schedule ID that doesn't exist on the network
    schedule_id = ScheduleId(0, 0, 999999999)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_SCHEDULE_ID"
    ):
        ScheduleInfoQuery(schedule_id).execute(env.client)
