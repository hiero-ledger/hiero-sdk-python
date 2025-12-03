"""
Integration tests for AccountRecordsQuery.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_account_record_query_can_execute(env):
    """Test that AccountRecordsQuery can execute."""
    account = env.create_account()

    # Perform transfer transaction
    transfer_receipt = (
        TransferTransaction()
        .add_hbar_transfer(account.id, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, -Hbar(1).to_tinybars())
        .execute(env.client)
    )
    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    # Query operator account records
    records = AccountRecordsQuery().set_account_id(env.operator_id).execute(env.client)

    assert len(records) > 0, f"Expected at least 1 record, but got {len(records)}"


@pytest.mark.integration
def test_integration_account_record_query_fails_with_invalid_account_id(env):
    """Test that AccountRecordsQuery fails with invalid account ID."""
    account_id = AccountId(0, 0, 999999999)

    with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_ACCOUNT_ID"):
        AccountRecordsQuery(account_id).execute(env.client)


@pytest.mark.integration
def test_integration_account_record_query_get_cost(env):
    """Test that AccountRecordsQuery can calculate query costs."""
    account = env.create_account()

    transfer_receipt = (
        TransferTransaction()
        .add_hbar_transfer(account.id, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, -Hbar(1).to_tinybars())
        .execute(env.client)
    )

    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    records_query = AccountRecordsQuery().set_account_id(account.id)

    cost = records_query.get_cost(env.client)

    records = records_query.set_query_payment(cost).execute(env.client)

    assert len(records) >= 0


@pytest.mark.integration
def test_integration_account_record_query_insufficient_payment(env):
    """Test that AccountRecordsQuery fails with insufficient payment."""
    account = env.create_account()

    transfer_receipt = (
        TransferTransaction()
        .add_hbar_transfer(account.id, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, -Hbar(1).to_tinybars())
        .execute(env.client)
    )

    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    records_query = AccountRecordsQuery().set_account_id(env.operator_id)

    with pytest.raises(PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"):
        records_query.set_query_payment(Hbar.from_tinybars(1)).execute(env.client)
