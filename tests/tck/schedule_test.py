"""Test cases for the getScheduleInfo TCK handler and its parameter parsing."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tck.handlers import registry, schedule as schedule_handlers
from tck.handlers.registry import parse_result
from tck.handlers.schedule import get_schedule_info
from tck.param.schedule import GetScheduleInfoParams
from tck.response.schedule import ScheduleInfoCostResponse, ScheduleInfoResponse


pytestmark = pytest.mark.unit


def _mock_schedule_info(**overrides):
    """A MagicMock standing in for a populated ScheduleInfo."""
    defaults = {
        "schedule_id": ScheduleId(0, 0, 100),
        "creator_account_id": AccountId(0, 0, 10),
        "payer_account_id": AccountId(0, 0, 20),
        "scheduled_transaction_id": TransactionId(AccountId(0, 0, 20), MagicMock(seconds=1700000000, nanos=0)),
        "signers": [],
        "admin_key": None,
        "expiration_time": MagicMock(seconds=1700000500),
        "executed_at": None,
        "deleted_at": None,
        "schedule_memo": "a memo",
        "wait_for_expiry": True,
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def _mock_query():
    """A MagicMock standing in for ScheduleInfoQuery's fluent setter chain."""
    query = MagicMock()
    query.set_grpc_deadline.return_value = query
    query.set_schedule_id.return_value = query
    query.set_query_payment.return_value = query
    query.set_max_query_payment.return_value = query
    return query


def test_get_schedule_info_is_registered():
    # Re-import to re-run the @rpc_method decorator, in case another test module's
    # teardown (e.g. handlers_test.py) cleared the shared registry after this module
    # was first imported.
    importlib.reload(schedule_handlers)
    handler = registry.get_handler("getScheduleInfo")
    assert handler is not None and callable(handler)


def test_parse_json_params():
    params = GetScheduleInfoParams.parse_json_params(
        {
            "sessionId": "session-1",
            "scheduleId": "0.0.100",
            "queryPayment": "1000",
            "maxQueryPayment": "5000",
            "getCost": True,
        }
    )

    assert params.scheduleId == "0.0.100"
    assert params.queryPayment == "1000"
    assert params.maxQueryPayment == "5000"
    assert params.getCost is True

    minimal = GetScheduleInfoParams.parse_json_params({"sessionId": "session-1"})
    assert minimal.scheduleId is None
    assert minimal.queryPayment is None
    assert minimal.maxQueryPayment is None
    assert minimal.getCost is None


def test_get_schedule_info_maps_fields():
    params = GetScheduleInfoParams(sessionId="session-1", scheduleId="0.0.100")
    query = _mock_query()
    query.execute.return_value = _mock_schedule_info()

    with (
        patch("tck.handlers.schedule.get_client", return_value=MagicMock()),
        patch("tck.handlers.schedule.ScheduleInfoQuery", return_value=query),
    ):
        result = get_schedule_info(params)

    query.set_schedule_id.assert_called_once_with(ScheduleId.from_string("0.0.100"))
    assert isinstance(result, ScheduleInfoResponse)
    assert result.scheduleId == "0.0.100"
    assert result.creatorAccountId == "0.0.10"
    assert result.payerAccountId == "0.0.20"
    assert result.scheduledTransactionId == "0.0.20@1700000000.0"
    assert result.expirationTime == "1700000500"
    assert result.scheduleMemo == "a memo"
    assert result.waitForExpiry is True


def test_get_schedule_info_keeps_nullable_fields_as_none():
    """A pending, non-deleted schedule must keep executedAt/deletedAt as None, not empty strings."""
    params = GetScheduleInfoParams(sessionId="session-1", scheduleId="0.0.100")
    query = _mock_query()
    query.execute.return_value = _mock_schedule_info(executed_at=None, deleted_at=None, admin_key=None)

    with (
        patch("tck.handlers.schedule.get_client", return_value=MagicMock()),
        patch("tck.handlers.schedule.ScheduleInfoQuery", return_value=query),
    ):
        result = get_schedule_info(params)

    assert result.executedAt is None
    assert result.deletedAt is None
    assert result.adminKey is None


def test_get_schedule_info_applies_query_payments():
    params = GetScheduleInfoParams(
        sessionId="session-1", scheduleId="0.0.100", queryPayment="1000", maxQueryPayment="5000"
    )
    query = _mock_query()
    query.execute.return_value = _mock_schedule_info()

    with (
        patch("tck.handlers.schedule.get_client", return_value=MagicMock()),
        patch("tck.handlers.schedule.ScheduleInfoQuery", return_value=query),
    ):
        get_schedule_info(params)

    query.set_query_payment.assert_called_once_with(Hbar.from_tinybars(1000))
    query.set_max_query_payment.assert_called_once_with(Hbar.from_tinybars(5000))


def test_get_schedule_info_get_cost_returns_cost_only():
    """getCost=true must return only the cost, without executing the full query."""
    params = GetScheduleInfoParams(sessionId="session-1", scheduleId="0.0.100", getCost=True)
    query = _mock_query()
    query.get_cost.return_value = Hbar.from_tinybars(250)

    with (
        patch("tck.handlers.schedule.get_client", return_value=MagicMock()),
        patch("tck.handlers.schedule.ScheduleInfoQuery", return_value=query),
    ):
        result = get_schedule_info(params)

    query.get_cost.assert_called_once()
    query.execute.assert_not_called()
    assert result == ScheduleInfoCostResponse(cost="250")

    # Dispatch-level: the JSON-RPC result must contain only "cost", not the
    # ScheduleInfoResponse fields (e.g. adminKey/executedAt/deletedAt nulls).
    assert parse_result(result) == {"cost": "250"}


def test_get_schedule_info_propagates_query_failure():
    """A non-existent scheduleId (INVALID_SCHEDULE_ID) must surface, not be swallowed."""
    params = GetScheduleInfoParams(sessionId="session-1", scheduleId="1000000.0.0")
    query = _mock_query()
    query.execute.side_effect = PrecheckError(status=1, transaction_id="0.0.1@1.1", message="INVALID_SCHEDULE_ID")

    with (
        patch("tck.handlers.schedule.get_client", return_value=MagicMock()),
        patch("tck.handlers.schedule.ScheduleInfoQuery", return_value=query),
        pytest.raises(PrecheckError),
    ):
        get_schedule_info(params)


def test_get_schedule_info_invalid_schedule_id_raises():
    """A malformed scheduleId should fail via ScheduleId.from_string before hitting the network."""
    params = GetScheduleInfoParams(sessionId="session-1", scheduleId="not-a-schedule-id")

    with patch("tck.handlers.schedule.get_client", return_value=MagicMock()), pytest.raises(ValueError):
        get_schedule_info(params)
