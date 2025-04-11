"""Tests for the TopicMessageSubmitTransaction functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hapi.services import (
    response_header_pb2, 
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2
)
from hiero_sdk_python.response_code import ResponseCode

from tests.mock_test import mock_hedera_servers

@pytest.fixture
def message():
    """Fixture to provide a test message."""
    return "Hello from topic submit!"


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


def test_topic_message_submit_transaction_retry_on_busy(topic_id, message):
    """Test that TopicMessageSubmitTransaction retries on BUSY response."""
    # First response is BUSY, second is OK
    busy_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )
    
    ok_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )
    
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                topicSequenceNumber=10 
            )
        )
    )
    
    response_sequences = [
        [busy_response, ok_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        client.max_attempts = 3
        
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(message)
        )
        
        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify transaction succeeded after retry
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.to_proto().topicSequenceNumber == 10
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"
        
        # Verify we didn't switch nodes (BUSY is retriable without node switch)
        assert client.node_account_id == AccountId(0, 0, 3), "Should not have switched nodes on BUSY"


def test_topic_message_submit_transaction_fails_on_nonretriable_error(topic_id, message):
    """Test that TopicMessageSubmitTransaction fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.INVALID_TOPIC_ID
    )
    
    response_sequences = [
        [error_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(message)
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.INVALID_TOPIC_ID) in str(exc_info.value)


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
