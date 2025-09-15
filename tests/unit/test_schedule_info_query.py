"""
Unit tests for the ScheduleInfoQuery class.
"""

from unittest.mock import Mock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    schedule_get_info_pb2,
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of ScheduleInfoQuery."""
    schedule_id = ScheduleId(0, 0, 100)

    query = ScheduleInfoQuery()
    assert query.schedule_id is None

    query = ScheduleInfoQuery(schedule_id)
    assert query.schedule_id == schedule_id


def test_set_schedule_id():
    """Test setting schedule ID with method chaining."""
    schedule_id = ScheduleId(0, 0, 100)
    query = ScheduleInfoQuery()

    result = query.set_schedule_id(schedule_id)

    assert result is query  # Should return self for chaining
    assert query.schedule_id == schedule_id


def test_execute_fails_with_missing_schedule_id(mock_client):
    """Test request creation with missing Schedule ID."""
    query = ScheduleInfoQuery()

    with pytest.raises(
        ValueError, match="Schedule ID must be set before making the request."
    ):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = ScheduleInfoQuery()

    mock_channel = Mock()
    mock_schedule_stub = Mock()
    mock_channel.schedule = mock_schedule_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_schedule_stub.getScheduleInfo


def test_schedule_info_query_execute(private_key):
    """Test basic functionality of ScheduleInfoQuery with mock server."""
    schedule_id = ScheduleId(0, 0, 100)
    creator_account_id = AccountId(0, 0, 100)
    payer_account_id = AccountId(0, 0, 101)
    expiration_time = TimestampProto(seconds=1718745600)
    scheduled_transaction_id = TransactionId.generate(creator_account_id)

    # Create schedule info response with test data
    schedule_info_response = schedule_get_info_pb2.ScheduleInfo(
        scheduleID=schedule_id._to_proto(),
        creatorAccountID=creator_account_id._to_proto(),
        payerAccountID=payer_account_id._to_proto(),
        expirationTime=expiration_time,
        scheduledTransactionID=scheduled_transaction_id._to_proto(),
        memo="test schedule memo",
        adminKey=private_key.public_key()._to_proto(),
        signers=KeyList(keys=[private_key.public_key()._to_proto()]),
        ledger_id=b"test_ledger_id",
        wait_for_expiry=True,
    )

    response_sequences = get_schedule_info_responses(schedule_info_response)

    with mock_hedera_servers(response_sequences) as client:
        query = ScheduleInfoQuery(schedule_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert result.schedule_id == schedule_id
        assert result.creator_account_id == creator_account_id
        assert result.payer_account_id == payer_account_id
        assert result.expiration_time == Timestamp._from_protobuf(expiration_time)
        assert result.executed_at is None
        assert result.deleted_at is None
        assert result.scheduled_transaction_id == scheduled_transaction_id
        assert result.schedule_memo == "test schedule memo"
        assert result.admin_key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert len(result.signers) == 1
        assert result.signers[0].to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.ledger_id == b"test_ledger_id"
        assert result.wait_for_expiry is True


def get_schedule_info_responses(schedule_info_response):
    """Helper function to create mock schedule info responses."""
    return [
        [
            response_pb2.Response(
                scheduleGetInfo=schedule_get_info_pb2.ScheduleGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                scheduleGetInfo=schedule_get_info_pb2.ScheduleGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                scheduleGetInfo=schedule_get_info_pb2.ScheduleGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    scheduleInfo=schedule_info_response,
                )
            ),
        ]
    ]
