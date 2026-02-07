import pytest
from unittest.mock import Mock, patch

from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_record import TransactionRecord
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
    assert result is query  # Should return self for chaining

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
        
def test_transaction_record_query_execute_with_duplicates(transaction_id):
    """Test TransactionRecordQuery returns duplicates when include_duplicates=True."""
    receipt = transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS)
    
    primary_record = transaction_record_pb2.TransactionRecord(
        receipt=receipt,
        memo="primary",
        transactionFee=100000,
    )
    
    duplicate_record = transaction_record_pb2.TransactionRecord(
        receipt=receipt,
        memo="duplicate",
        transactionFee=100000,     
    )

    response_sequences = [[
        # Cost query responses...
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
                ),
                transactionRecord=primary_record,
                duplicateTransactionRecords=[duplicate_record]
            )
        )
    ]]
    
    with mock_hedera_servers(response_sequences) as client:
        query = TransactionRecordQuery(transaction_id, include_duplicates=True)
        result = query.execute(client)
        
        assert isinstance(result, TransactionRecord), "Primary result must be TransactionRecord"
        assert result.transaction_memo == "primary"
        assert hasattr(result, 'duplicates'), "duplicates attribute must exist"
        assert len(result.duplicates) == 1
        assert result.duplicates[0].transaction_memo == "duplicate"
        assert isinstance(result.duplicates[0], TransactionRecord)
        assert result.duplicates[0].transaction_id == transaction_id
        
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
        
        with pytest.raises(AttributeError):
            query._make_request()


# ────────────────────────────────────────────────────────────────
# Unit tests for _map_record_list
# ────────────────────────────────────────────────────────────────

def test_map_record_list_converts_protobuf_list(transaction_id):
    """_map_record_list should convert each proto record using TransactionRecord._from_proto."""
    # Create actual proto records with distinct data
    receipt = transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS)
    proto_record_1 = transaction_record_pb2.TransactionRecord(
        receipt=receipt,
        memo="record1",
        transactionFee=100
    )
    proto_record_2 = transaction_record_pb2.TransactionRecord(
        receipt=receipt,
        memo="record2",
        transactionFee=200
    )

    query = TransactionRecordQuery(transaction_id=transaction_id)
    result = query._map_record_list([proto_record_1, proto_record_2])
    
    assert len(result) == 2
    # Verify actual TransactionRecord instances are returned
    assert isinstance(result[0], TransactionRecord)
    assert isinstance(result[1], TransactionRecord)
    # Verify transaction_id was propagated
    assert result[0].transaction_id == transaction_id
    assert result[1].transaction_id == transaction_id
    # Verify data was correctly mapped
    assert result[0].transaction_memo == "record1"
    assert result[1].transaction_memo == "record2"

def test_map_record_list_handles_empty_list(transaction_id):
    """_map_record_list returns empty list for empty input."""
    query = TransactionRecordQuery(transaction_id=transaction_id)
    
    result = query._map_record_list([])
    
    assert result == []
    assert isinstance(result, list)

# === Type validation / error handling tests ===

def test_set_include_duplicates_raises_on_invalid_type():
    """set_include_duplicates rejects non-boolean values."""
    query = TransactionRecordQuery()
    
    with pytest.raises(TypeError) as exc:
        query.set_include_duplicates(42)  # wrong type: int
    msg = str(exc.value)
    assert "include_duplicates must be a boolean" in msg
    assert "got int" in msg


def test_init_raises_on_invalid_include_duplicates_type():
    """__init__ rejects non-boolean include_duplicates."""
    with pytest.raises(TypeError) as exc:
        TransactionRecordQuery(
            transaction_id=None,
            include_duplicates="yes"  # wrong type: str
        )
    msg = str(exc.value)
    assert "include_duplicates must be a bool" in msg           
    assert "(True or False)" in msg                             # optional: extra safety
    assert "got str" in msg                                     # optional: checks type name


def test_set_transaction_id_raises_on_invalid_type():
    """set_transaction_id rejects invalid types for transaction_id."""
    query = TransactionRecordQuery()
    
    with pytest.raises(TypeError) as exc:
        query.set_transaction_id(["not", "a", "txid"])  # wrong type: list
    msg = str(exc.value)
    assert "transaction_id must be TransactionId or None" in msg
    assert "got list" in msg
