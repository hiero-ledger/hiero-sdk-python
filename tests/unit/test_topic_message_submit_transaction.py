"""Tests for the TopicMessageSubmitTransaction functionality."""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
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
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

@pytest.fixture
def message():
    """Fixture to provide a test message."""
    return "Hello from topic submit!"


@pytest.fixture
def custom_fee_limit():
    """Fixture for a CustomFeeLimit object."""
    return CustomFeeLimit()


def test_constructor_and_setters(topic_id, message, custom_fee_limit):
    """Test constructor and all setter methods."""
    # Test constructor with parameters
    tx = TopicMessageSubmitTransaction(topic_id=topic_id, message=message)
    assert tx.topic_id == topic_id
    assert tx.message == message

    # Test constructor with default values
    tx_default = TopicMessageSubmitTransaction()
    assert tx_default.topic_id is None
    assert tx_default.message is None

    # Test set_topic_id
    result = tx_default.set_topic_id(topic_id)
    assert tx_default.topic_id == topic_id
    assert result is tx_default

    # Test set_message
    result = tx_default.set_message(message)
    assert tx_default.message == message
    assert result is tx_default

    # Test set_custom_fee_limits
    custom_fee_limits = [custom_fee_limit]
    result = tx_default.set_custom_fee_limits(custom_fee_limits)
    assert tx_default.custom_fee_limits == custom_fee_limits
    assert result is tx_default

    # Test set_custom_fee_limits to empty list
    result = tx_default.set_custom_fee_limits([])
    assert tx_default.custom_fee_limits == []
    assert result is tx_default

    # Test add_custom_fee_limit
    result = tx_default.add_custom_fee_limit(custom_fee_limit)
    assert len(tx_default.custom_fee_limits) == 1
    assert tx_default.custom_fee_limits[0] == custom_fee_limit
    assert result is tx_default


def test_set_methods_require_not_frozen(
    mock_client, topic_id, message, custom_fee_limit
):
    """Test that setter methods raise exception when transaction is frozen."""
    tx = TopicMessageSubmitTransaction(topic_id=topic_id, message=message)
    tx.freeze_with(mock_client)

    test_cases = [
        ("set_topic_id", topic_id),
        ("set_message", message),
        ("set_custom_fee_limits", [custom_fee_limit]),
        ("add_custom_fee_limit", custom_fee_limit),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(tx, method_name)(value)


def test_method_chaining(topic_id, message, custom_fee_limit):
    """Test method chaining functionality."""
    tx = TopicMessageSubmitTransaction()

    result = (
        tx.set_topic_id(topic_id)
        .set_message(message)
        .set_custom_fee_limits([custom_fee_limit])
        .add_custom_fee_limit(custom_fee_limit)
    )

    assert result is tx
    assert tx.topic_id == topic_id
    assert tx.message == message
    assert len(tx.custom_fee_limits) == 2


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    tx = TopicMessageSubmitTransaction()

    mock_channel = MagicMock()
    mock_topic_stub = MagicMock()
    mock_channel.topic = mock_topic_stub

    method = tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_topic_stub.submitMessage


# This test uses fixtures (topic_id, message) as parameters
def test_build_scheduled_body(topic_id, message):
    """Test building a schedulable TopicMessageSubmitTransaction body."""
    # Create transaction with all required fields
    tx = TopicMessageSubmitTransaction()
    tx.set_topic_id(topic_id)
    tx.set_message(message)
    
    # Build the scheduled body
    schedulable_body = tx.build_scheduled_body()
    
    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    
    # Verify the transaction was built with topic message submit type
    assert schedulable_body.HasField("consensusSubmitMessage")
    
    # Verify fields in the schedulable body
    assert schedulable_body.consensusSubmitMessage.topicID.topicNum == 1234
    assert schedulable_body.consensusSubmitMessage.message == bytes(message, 'utf-8')

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
