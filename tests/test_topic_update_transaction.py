"""Tests for the TopicUpdateTransaction functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
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

@pytest.mark.usefixtures("mock_account_ids")
def test_build_topic_update_transaction_body(mock_account_ids, topic_id):
    """Test building a TopicUpdateTransaction body with valid topic ID and memo."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicUpdateTransaction(topic_id=topic_id, memo="Updated Memo")

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()
    assert transaction_body.consensusUpdateTopic.topicID.topicNum == 1234
    assert transaction_body.consensusUpdateTopic.memo.value == "Updated Memo"


def test_missing_topic_id_in_update(mock_account_ids):
    """Test that building fails if no topic ID is provided."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicUpdateTransaction(topic_id=None, memo="No ID")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required fields"):
        tx.build_transaction_body()


def test_sign_topic_update_transaction(mock_account_ids, topic_id, private_key):
    """Test signing the TopicUpdateTransaction with a private key."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicUpdateTransaction(topic_id=topic_id, memo="Signature test")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx.transaction_body_bytes = body_bytes

    tx.sign(private_key)
    assert len(tx.signature_map.sigPair) == 1


def test_execute_topic_update_transaction(topic_id):
    """Test executing the TopicUpdateTransaction successfully with mock server."""
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
            TopicUpdateTransaction()
            .set_topic_id(topic_id)
            .set_memo("Updated with mock server")
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS


def test_topic_update_transaction_fails_on_nonretriable_error(topic_id):
    """Test that TopicUpdateTransaction fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.UNAUTHORIZED
    )
    
    response_sequences = [
        [error_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        tx = (
            TopicUpdateTransaction()
            .set_topic_id(topic_id)
            .set_memo("Update with error")
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.UNAUTHORIZED) in str(exc_info.value)


def test_topic_update_transaction_with_all_fields(topic_id, private_key):
    """Test updating a topic with all available fields."""
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
        admin_key = PrivateKey.generate().public_key()
        submit_key = PrivateKey.generate().public_key()
        auto_renew_account = AccountId(0, 0, 5678)
        
        tx = (
            TopicUpdateTransaction()
            .set_topic_id(topic_id)
            .set_memo("Comprehensive update")
            .set_admin_key(admin_key)
            .set_submit_key(submit_key)
            .set_auto_renew_period(Duration(7776000))  # 90 days
            .set_auto_renew_account(auto_renew_account)
        )
        
        try:
            transaction = tx.execute(client)
            receipt = transaction.get_receipt(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS
