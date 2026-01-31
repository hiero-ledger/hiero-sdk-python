import pytest
from unittest.mock import Mock, patch, MagicMock

from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2,
    response_header_pb2,
    transaction_get_record_pb2,
    transaction_record_pb2,
    transaction_receipt_pb2,
    query_pb2,
    query_header_pb2,
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_constructor(transaction_id):
    """Test initialization of TransactionRecordQuery."""
    query = TransactionRecordQuery()
    assert query.transaction_id is None
    
    query = TransactionRecordQuery(transaction_id)
    assert query.transaction_id == transaction_id

def test_set_transaction_id(transaction_id):
    """Test setting transaction ID."""
    query = TransactionRecordQuery()
    result = query.set_transaction_id(transaction_id)
    
    assert query.transaction_id == transaction_id
    assert result == query  # Should return self for chaining

def test_set_include_duplicates_chaining_and_validation():
    """Test set_include_duplicates: correct assignment, chaining, and type validation."""
    query = TransactionRecordQuery()
    assert query.include_duplicates is False

    query_true = TransactionRecordQuery(include_duplicates=True)
    assert query_true.include_duplicates is True

    # Positive cases: valid boolean values + chaining
    result = query.set_include_duplicates(True)
    assert result is query                      # chaining works
    assert query.include_duplicates is True

    result = query.set_include_duplicates(False)
    assert result is query
    assert query.include_duplicates is False

    # Negative case: non-boolean input raises TypeError
    with pytest.raises(TypeError, match="include_duplicates must be a boolean"):
        query.set_include_duplicates("not a bool")

    with pytest.raises(TypeError, match="include_duplicates must be a boolean"):
        query.set_include_duplicates(123)

    with pytest.raises(TypeError, match="include_duplicates must be a boolean"):
        query.set_include_duplicates(None)

def test_execute_fails_with_missing_transaction_id(mock_client):
    """Test request creation with missing Transaction ID."""
    query = TransactionRecordQuery()
    
    with pytest.raises(ValueError, match="Transaction ID must be set before making the request."):
        query.execute(mock_client)

def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = TransactionRecordQuery()
    
    mock_channel = Mock()
    mock_crypto_stub = Mock()
    mock_channel.crypto = mock_crypto_stub
    
    method = query._get_method(mock_channel)
    
    assert method.transaction is None
    assert method.query == mock_crypto_stub.getTxRecordByTxID

def test_is_payment_required():
    """Test that transaction record query doesn't require payment."""
    query = TransactionRecordQuery()
    assert query._is_payment_required() is True

def test_transaction_record_query_execute(transaction_id):
    """Test basic functionality of TransactionRecordQuery with mock server."""
    # Create a mock transaction receipt
    receipt = transaction_receipt_pb2.TransactionReceipt(
        status=ResponseCode.SUCCESS
    )
    
    # Create a mock transaction record
    transaction_record = transaction_record_pb2.TransactionRecord(
        receipt=receipt,
        transactionHash=b'\x01' * 48,
        transactionID=transaction_id._to_proto(),
        memo="Test transaction",
        transactionFee=100000
    )

    response_sequences = get_transaction_record_responses(transaction_record)
    
    with mock_hedera_servers(response_sequences) as client:
        query = TransactionRecordQuery(transaction_id)
        
        try:
            # Get the cost of executing the query - should be 2 tinybars based on the mock response
            cost = query.get_cost(client)
            assert cost.to_tinybars() == 2
            
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        assert result.transaction_id == transaction_id
        assert result.receipt.status == ResponseCode.SUCCESS
        assert result.transaction_fee == 100000
        assert result.transaction_hash == b'\x01' * 48
        assert result.transaction_memo == "Test transaction"
        
def get_transaction_record_responses(transaction_record):
        return [[
            response_pb2.Response(
                transactionGetRecord=transaction_get_record_pb2.TransactionGetRecordResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2
                    )
                )
            ),
            response_pb2.Response(
                transactionGetRecord=transaction_get_record_pb2.TransactionGetRecordResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2
                    )
                )
            ),
            response_pb2.Response(
                transactionGetRecord=transaction_get_record_pb2.TransactionGetRecordResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2
                    ),
                    transactionRecord=transaction_record
                )
            )
        ]]
# ────────────────────────────────────────────────────────────────
# Unit tests for _make_request (protobuf construction)
# ────────────────────────────────────────────────────────────────

@patch.object(TransactionRecordQuery, '_make_request_header')
def test_make_request_constructs_correct_protobuf(mock_make_header, transaction_id):
    """Test that _make_request builds valid TransactionGetRecordQuery protobuf."""
    # Mock the header that normally comes from Query base class
    fake_header = query_header_pb2.QueryHeader(
        responseType=ResponseType.ANSWER_STATE_PROOF,
        nodeTransactionPrecheckCode=ResponseCode.OK,
    )
    mock_make_header.return_value = fake_header

    query = TransactionRecordQuery(transaction_id=transaction_id)
    query.include_duplicates = False  # default

    proto_query = query._make_request()

    assert isinstance(proto_query, query_pb2.Query)
    assert proto_query.HasField("transactionGetRecord")

    tgr = proto_query.transactionGetRecord
    assert tgr.header == fake_header
    assert tgr.transactionID == transaction_id._to_proto()
    assert tgr.includeDuplicates is False


@patch.object(TransactionRecordQuery, '_make_request_header')
def test_make_request_sets_include_duplicates_true(mock_make_header, transaction_id):
    """Verify includeDuplicates flag is correctly passed to protobuf."""
    fake_header = query_header_pb2.QueryHeader()
    mock_make_header.return_value = fake_header

    query = TransactionRecordQuery(transaction_id=transaction_id)
    query.include_duplicates = True

    proto_query = query._make_request()
    tgr = proto_query.transactionGetRecord

    assert tgr.includeDuplicates is True


def test_make_request_raises_when_no_transaction_id():
    """Missing transaction_id should raise clear ValueError."""
    query = TransactionRecordQuery()
    with pytest.raises(ValueError, match="Transaction ID must be set"):
        query._make_request()


@patch.object(TransactionRecordQuery, '_make_request_header')
def test_make_request_checks_for_transactionGetRecord_field(mock_make_header, transaction_id):
    """Regression check: fails if protobuf structure changes and field is missing."""
    fake_header = query_header_pb2.QueryHeader()
    mock_make_header.return_value = fake_header

    query = TransactionRecordQuery(transaction_id=transaction_id)

    # Simulate broken generated protobuf (rare but good safety net)
    with patch("hiero_sdk_python.hapi.services.query_pb2.Query") as mock_query_cls:
        mock_query_cls.return_value = object()  # no attributes: deterministic AttributeError
        
        with pytest.raises(AttributeError, match="no attribute 'transactionGetRecord'"):
            query._make_request()


# ────────────────────────────────────────────────────────────────
# Unit tests for _map_record_list
# ────────────────────────────────────────────────────────────────

def test_map_record_list_converts_protobuf_list(transaction_id):
    """_map_record_list should convert each proto record using TransactionRecord._from_proto."""
    proto_record_1 = transaction_record_pb2.TransactionRecord()
    proto_record_2 = transaction_record_pb2.TransactionRecord()

    fake_records = [proto_record_1, proto_record_2]

    query = TransactionRecordQuery(transaction_id=transaction_id)

    with patch("hiero_sdk_python.transaction.transaction_record.TransactionRecord._from_proto") as mock_from_proto:
        # Simulate what _from_proto returns
        mock_from_proto.side_effect = [
            MagicMock(transaction_id=transaction_id, memo="record1"),
            MagicMock(transaction_id=transaction_id, memo="record2"),
        ]

        result = query._map_record_list(fake_records)

    assert len(result) == 2
    assert mock_from_proto.call_count == 2

    # Verify returned objects are the ones from _from_proto
    assert result[0].memo == "record1"
    assert result[1].memo == "record2"

    # Verify it passes the correct transaction_id every time
    for call in mock_from_proto.call_args_list:
        assert call.kwargs["transaction_id"] == transaction_id

def test_map_record_list_handles_empty_list(transaction_id):
    """_map_record_list returns empty list for empty input."""
    query = TransactionRecordQuery(transaction_id=transaction_id)
    
    result = query._map_record_list([])
    
    assert result == []
    assert isinstance(result, list)
