"""Tests for the TopicDeleteTransaction functionality."""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.hapi.services import (
    response_header_pb2, 
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.response_code import ResponseCode

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixtures (mock_account_ids, topic_id) as parameters
def test_build_topic_delete_transaction_body(mock_account_ids, topic_id):
    """Test building a TopicDeleteTransaction body with a valid topic ID."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=topic_id)

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()
    assert transaction_body.consensusDeleteTopic.topicID.topicNum == 1234
    
# This test uses fixtures (mock_account_ids, topic_id) as parameters
def test_build_scheduled_body(mock_account_ids, topic_id):
    """Test building a schedulable TopicDeleteTransaction body with a valid topic ID."""
    _, _, node_account_id, _, _ = mock_account_ids
    
    # Create transaction and set required fields
    tx = TopicDeleteTransaction()
    tx.set_topic_id(topic_id)
    
    # Build the scheduled body
    schedulable_body = tx.build_scheduled_body()
    
    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    
    # Verify the transaction was built with topic delete type
    assert schedulable_body.HasField("consensusDeleteTopic")
    
    # Verify the topic ID was correctly set
    assert schedulable_body.consensusDeleteTopic.topicID.topicNum == 1234

# This test uses fixture mock_account_ids as parameter
def test_missing_topic_id_in_delete(mock_account_ids):
    """Test that building fails if no topic ID is provided."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=None)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required fields"):
        tx.build_transaction_body()

# This test uses fixtures (mock_account_ids, topic_id, private_key) as parameters
def test_sign_topic_delete_transaction(mock_account_ids, topic_id, private_key):
    """Test signing the TopicDeleteTransaction with a private key."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=topic_id)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx._transaction_body_bytes.setdefault(node_account_id, body_bytes)

    tx.sign(private_key)
    assert len(tx._signature_map[body_bytes].sigPair) == 1

# This test uses fixture topic_id as parameter
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
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS