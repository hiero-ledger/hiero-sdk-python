"""
Integration tests for ScheduleSignTransaction.
"""

import pytest

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.schedule.schedule_sign_transaction import ScheduleSignTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_schedule_sign_transaction_can_execute(env):
    """Test that ScheduleSignTransaction can execute."""
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
        .set_schedule_memo("test schedule sign transaction")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert (
        schedule_info.admin_key.to_bytes_raw()
        == env.operator_key.public_key().to_bytes_raw()
    )
    assert not schedule_info.signers
    assert schedule_info.executed_at is None  # Check it is not executed
    assert schedule_info.deleted_at is None

    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(schedule_id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule sign transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert len(schedule_info.signers) == 1
    assert (
        schedule_info.signers[0].to_bytes_raw()
        == account.key.public_key().to_bytes_raw()
    )
    assert schedule_info.executed_at is not None  # Check it executed
    assert schedule_info.deleted_at is None


def test_integration_schedule_sign_transaction_can_execute_multiple_signers(env):
    """Test that ScheduleSignTransaction can execute with multiple signers."""
    account = env.create_account()
    payer_account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )
    receipt = (
        schedule_create_tx.set_payer_account_id(payer_account.id)
        .set_schedule_memo("test schedule sign transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"
    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert not schedule_info.signers
    assert schedule_info.executed_at is None

    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(schedule_id)
        .freeze_with(env.client)
        .sign(account.key)
        .sign(payer_account.key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule sign transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert len(schedule_info.signers) == 2
    
    signers = [s.to_bytes_raw() for s in schedule_info.signers]
    assert account.key.public_key().to_bytes_raw() in signers
    
    assert schedule_info.executed_at is not None


def test_integration_schedule_sign_transaction_add_signer_later(env):
    """Test that ScheduleSignTransaction can add a signer later."""
    account = env.create_account()

    receipt = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
        .set_schedule_memo("test schedule sign transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"

    assert receipt.schedule_id is not None
    assert receipt.scheduled_transaction_id is not None
    schedule_id = receipt.schedule_id

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert len(schedule_info.signers) == 1
    assert (
        schedule_info.signers[0].to_bytes_raw()
        == env.operator_key.public_key().to_bytes_raw()
    )
    assert schedule_info.executed_at is None

    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(schedule_id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Schedule sign transaction failed with status: {ResponseCode(receipt.status).name}"

    schedule_info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(env.client)
    assert schedule_info is not None
    assert schedule_info.schedule_id == schedule_id
    assert len(schedule_info.signers) == 2

    signers = [s.to_bytes_raw() for s in schedule_info.signers]
    assert env.operator_key.public_key().to_bytes_raw() in signers
    assert account.key.public_key().to_bytes_raw() in signers

    assert schedule_info.executed_at is not None


def test_integration_schedule_sign_transaction_fails_invalid_schedule_id(env):
    """Test that ScheduleSignTransaction fails with an invalid schedule ID."""
    schedule_id = ScheduleId(0, 0, 999999999)

    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(schedule_id)
        .freeze_with(env.client)
        .sign(env.operator_key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.INVALID_SCHEDULE_ID, (
        f"Schedule sign transaction should have failed with INVALID_SCHEDULE_ID status but got: "
        f"{ResponseCode(receipt.status).name}"
    )

def test_integration_schedule_sign_transaction_fails_with_already_executed(env):
    """Test that ScheduleSignTransaction fails when the schedule has already been executed."""
    account = env.create_account()

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(account.id, -1000)  # 1000 tinybars
        .add_hbar_transfer(env.operator_id, 1000)
        .schedule()
    )

    receipt = (
        schedule_create_tx.set_payer_account_id(account.id)
        .set_schedule_memo("test schedule sign transaction")
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"

    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(receipt.schedule_id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SCHEDULE_ALREADY_EXECUTED, (
        f"Schedule sign transaction should have failed with "
        f"SCHEDULE_ALREADY_EXECUTED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )
