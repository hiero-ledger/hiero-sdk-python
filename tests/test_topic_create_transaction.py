"""Tests for the TopicCreateTransaction functionality."""

import pytest
from unittest.mock import patch
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2, 
    transaction_get_receipt_pb2,
    transaction_response_pb2,
    transaction_receipt_pb2
)

from tests.mock_test import mock_hedera_servers

@pytest.mark.usefixtures("mock_account_ids")
def test_build_topic_create_transaction_body(mock_account_ids):
    """
    Test building a TopicCreateTransaction body with valid memo, admin key.
    """
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction(memo="Hello Topic", admin_key=PrivateKey.generate().public_key())

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()

    assert transaction_body.consensusCreateTopic.memo == "Hello Topic"
    assert transaction_body.consensusCreateTopic.adminKey.ed25519

def test_missing_operator_in_topic_create(mock_account_ids):
    """
    Test that building the body fails if no operator ID is set.
    """
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction(memo="No Operator")
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Operator account ID is not set."):
        tx.build_transaction_body()

def test_missing_node_in_topic_create(mock_account_ids):
    """
    Test that building the body fails if no node account ID is set.
    """
    tx = TopicCreateTransaction(memo="No Node")
    tx.operator_account_id = AccountId(0, 0, 2)

    with pytest.raises(ValueError, match="Node account ID is not set."):
        tx.build_transaction_body()

def test_sign_topic_create_transaction(mock_account_ids, private_key):
    """
    Test signing the TopicCreateTransaction with a private key.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicCreateTransaction(memo="Signing test")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx.transaction_body_bytes = body_bytes

    tx.sign(private_key)
    assert len(tx.signature_map.sigPair) == 1

def test_execute_topic_create_transaction():
    """Test executing the TopicCreateTransaction successfully with mock server."""
    # Create success response for the transaction submission
    tx_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )
    
    # Create receipt response with SUCCESS status and a topic ID
    topic_id = basic_types_pb2.TopicID(
        shardNum=0,
        realmNum=0,
        topicNum=123
    )
    
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                topicID=topic_id
            )
        )
    )
    
    response_sequences = [
        [tx_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client:
        tx = (
            TopicCreateTransaction()
            .set_memo("Execute test with mock server")
            .set_admin_key(PrivateKey.generate().public_key())
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS
        assert isinstance(receipt.topicId, TopicId)
        assert receipt.topicId.shard == 0
        assert receipt.topicId.realm == 0
        assert receipt.topicId.num == 123

def test_topic_create_transaction_retry_on_busy():
    """Test that TopicCreateTransaction retries on BUSY response."""
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
                topicID=basic_types_pb2.TopicID(
                    shardNum=0,
                    realmNum=0,
                    topicNum=456
                )
            )
        )
    )
    
    response_sequences = [
        [busy_response, ok_response, receipt_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        client.max_attempts = 3
        
        tx = (
            TopicCreateTransaction()
            .set_memo("Test with retry")
            .set_admin_key(PrivateKey.generate().public_key())
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        # Verify transaction succeeded after retry
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.topicId.num == 456
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"
        
        # Verify we didn't switch nodes (BUSY is retriable without node switch)
        assert client.node_account_id == AccountId(0, 0, 3), "Should not have switched nodes on BUSY"

def test_topic_create_transaction_fails_on_nonretriable_error():
    """Test that TopicCreateTransaction fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION_BODY
    )
    
    response_sequences = [
        [error_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        tx = (
            TopicCreateTransaction()
            .set_memo("Test with error")
            .set_admin_key(PrivateKey.generate().public_key())
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.INVALID_TRANSACTION_BODY) in str(exc_info.value)
