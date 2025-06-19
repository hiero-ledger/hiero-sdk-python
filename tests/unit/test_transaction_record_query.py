import pytest
from unittest.mock import Mock

from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2,
    response_header_pb2,
    transaction_get_record_pb2,
    transaction_record_pb2,
    transaction_receipt_pb2,
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