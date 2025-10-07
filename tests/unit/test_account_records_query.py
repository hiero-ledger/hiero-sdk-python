"""
Unit tests for the AccountRecordsQuery class.
"""

from unittest.mock import Mock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_receipt_pb2,
    transaction_record_pb2,
)
from hiero_sdk_python.hapi.services.crypto_get_account_records_pb2 import (
    CryptoGetAccountRecordsResponse,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of AccountRecordsQuery."""
    account_id = AccountId(0, 0, 2)

    query = AccountRecordsQuery()
    assert query.account_id is None

    query = AccountRecordsQuery().set_account_id(account_id)
    assert query.account_id == account_id


def test_execute_fails_with_missing_account_id(mock_client):
    """Test request creation with missing Account ID."""
    query = AccountRecordsQuery()

    with pytest.raises(ValueError, match="Account ID must be set before making the request."):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = AccountRecordsQuery()

    mock_channel = Mock()
    mock_crypto_stub = Mock()
    mock_channel.crypto = mock_crypto_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_crypto_stub.getAccountRecords


def test_account_record_query_execute(mock_account_ids):
    """Test basic functionality of AccountRecordsQuery with mock server."""
    account_id = mock_account_ids[0]
    consensus_timestamp = TimestampProto(seconds=1718745600, nanos=123456789)

    # Create transaction record response with test data
    transaction_record = transaction_record_pb2.TransactionRecord(
        transactionID=basic_types_pb2.TransactionID(
            accountID=account_id._to_proto(), transactionValidStart=consensus_timestamp
        ),
        consensusTimestamp=consensus_timestamp,
        transactionFee=25,
        memo="test memo",
        receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transactionHash=b"test_hash",
    )

    response_sequences = get_account_record_responses([transaction_record])

    with mock_hedera_servers(response_sequences) as client:
        query = AccountRecordsQuery().set_account_id(account_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert len(result) == 1, f"Expected 1 record, but got {len(result)}"
        record = result[0]

        assert record.transaction_fee == 25
        assert record.transaction_memo == "test memo"
        assert record.transaction_hash == b"test_hash"


def test_account_record_query_multiple_records(mock_account_ids):
    """Test AccountRecordsQuery with multiple transaction records."""
    account_id = mock_account_ids[0]
    consensus_timestamp1 = TimestampProto(seconds=1718745600, nanos=123456789)
    consensus_timestamp2 = TimestampProto(seconds=1718745700, nanos=987654321)

    # Create multiple transaction records
    record1 = transaction_record_pb2.TransactionRecord(
        transactionID=basic_types_pb2.TransactionID(
            accountID=account_id._to_proto(), transactionValidStart=consensus_timestamp1
        ),
        consensusTimestamp=consensus_timestamp1,
        transactionFee=25,
        memo="account creation",
        receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transactionHash=b"hash1",
    )

    record2 = transaction_record_pb2.TransactionRecord(
        transactionID=basic_types_pb2.TransactionID(
            accountID=account_id._to_proto(), transactionValidStart=consensus_timestamp2
        ),
        consensusTimestamp=consensus_timestamp2,
        transactionFee=5,
        memo="transfer",
        receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transactionHash=b"hash2",
    )

    response_sequences = get_account_record_responses([record1, record2])

    with mock_hedera_servers(response_sequences) as client:
        query = AccountRecordsQuery().set_account_id(account_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert len(result) == 2, f"Expected 2 records, but got {len(result)}"

        # Verify first record
        assert result[0].transaction_memo == "account creation"
        assert result[0].transaction_fee == 25
        assert result[0].transaction_hash == b"hash1"

        # Verify second record
        assert result[1].transaction_memo == "transfer"
        assert result[1].transaction_fee == 5
        assert result[1].transaction_hash == b"hash2"


def test_account_record_query_empty_records(mock_account_ids):
    """Test AccountRecordsQuery with no transaction records."""
    account_id = mock_account_ids[0]

    response_sequences = get_account_record_responses([])

    with mock_hedera_servers(response_sequences) as client:
        query = AccountRecordsQuery().set_account_id(account_id)

        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert len(result) == 0, f"Expected 0 records, but got {len(result)}"
        assert isinstance(result, list), "Expected result to be a list"


def get_account_record_responses(transaction_records):
    """Helper function to create mock responses for account record queries."""
    return [
        [
            response_pb2.Response(
                cryptoGetAccountRecords=CryptoGetAccountRecordsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                cryptoGetAccountRecords=CryptoGetAccountRecordsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                cryptoGetAccountRecords=CryptoGetAccountRecordsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    records=transaction_records,
                )
            ),
        ]
    ]
