"""Tests for the TopicDeleteTransaction functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2, 
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2
)
from hiero_sdk_python.response_code import ResponseCode

from tests.mock_test import mock_hedera_servers

@pytest.mark.usefixtures("mock_account_ids")
def test_build_topic_delete_transaction_body(mock_account_ids, topic_id):
    """Test building a TopicDeleteTransaction body with a valid topic ID."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=topic_id)

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()
    assert transaction_body.consensusDeleteTopic.topicID.topicNum == 1234


def test_missing_topic_id_in_delete(mock_account_ids):
    """Test that building fails if no topic ID is provided."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=None)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required fields"):
        tx.build_transaction_body()


def test_sign_topic_delete_transaction(mock_account_ids, topic_id, private_key):
    """Test signing the TopicDeleteTransaction with a private key."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=topic_id)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx.transaction_body_bytes = body_bytes

    tx.sign(private_key)
    assert len(tx.signature_map.sigPair) == 1


def test_execute_topic_delete_transaction(topic_id):
    """Test executing the TopicDeleteTransaction successfully with mock server."""
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
            TopicDeleteTransaction()
            .set_topic_id(topic_id)
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS


def test_topic_delete_transaction_retry_on_busy(topic_id):
    """Test that TopicDeleteTransaction retries on BUSY response."""
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
                status=ResponseCode.SUCCESS
            )
        )
    )
    
    response_sequences = [
        [busy_response, ok_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        client.max_attempts = 3
        
        tx = (
            TopicDeleteTransaction()
            .set_topic_id(topic_id)
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify transaction succeeded after retry
        assert receipt.status == ResponseCode.SUCCESS
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"
        
        # Verify we didn't switch nodes (BUSY is retriable without node switch)
        assert client.node_account_id == AccountId(0, 0, 3), "Should not have switched nodes on BUSY"


def test_topic_delete_transaction_fails_on_nonretriable_error(topic_id):
    """Test that TopicDeleteTransaction fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.UNAUTHORIZED
    )
    
    response_sequences = [
        [error_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        tx = (
            TopicDeleteTransaction()
            .set_topic_id(topic_id)
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.UNAUTHORIZED) in str(exc_info.value)
