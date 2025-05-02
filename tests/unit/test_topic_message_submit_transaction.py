"""Tests for the TopicMessageSubmitTransaction functionality."""

import pytest

from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.hapi.services import (
    response_header_pb2, 
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2
)
from hiero_sdk_python.response_code import ResponseCode

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

@pytest.fixture
def message():
    """Fixture to provide a test message."""
    return "Hello from topic submit!"

# This test uses fixtures (topic_id, message) as parameters
def test_execute_topic_message_submit_transaction(topic_id, message):
    """Test executing the TopicMessageSubmitTransaction successfully with mock server."""
    # Create success response for the transaction submission
    tx_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )
    
    # Create receipt response with SUCCESS status
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            )
        )
    )
    
    response_sequences = [
        [tx_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client:
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(message)
        )
        
        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS


# This test uses fixture topic_id as parameter
def test_topic_message_submit_transaction_with_large_message(topic_id):
    """Test sending a large message (close to the maximum allowed size)."""
    # Create a large message (just under the typical 4KB limit)
    large_message = "A" * 4000
    
    # Create success responses
    tx_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )
    
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            )
        )
    )
    
    response_sequences = [
        [tx_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client:
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(large_message)
        )
        
        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS
