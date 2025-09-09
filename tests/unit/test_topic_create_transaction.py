"""Tests for the TopicCreateTransaction functionality."""

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2, 
    transaction_get_receipt_pb2,
    transaction_response_pb2,
    transaction_receipt_pb2
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture mock_account_ids as parameter
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
    
def test_build_scheduled_body(mock_account_ids):
    """
    Test building a scheduled body for TopicCreateTransaction with valid properties.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    
    # Create private key for the admin key
    admin_key = PrivateKey.generate().public_key()
    submit_key = PrivateKey.generate().public_key()
    
    # Create a transaction with all fields set
    tx = TopicCreateTransaction()
    tx.set_memo("Scheduled Topic")
    tx.set_admin_key(admin_key)
    tx.set_submit_key(submit_key)
    tx.set_auto_renew_account(AccountId(0, 0, 5))
    
    # Build the scheduled transaction body
    schedulable_body = tx.build_scheduled_body()
    
    # Verify it's the right type
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    
    # Verify the transaction was built with the topic create type
    assert schedulable_body.HasField("consensusCreateTopic")
    
    # Verify fields in the scheduled body
    assert schedulable_body.consensusCreateTopic.memo == "Scheduled Topic"
    assert schedulable_body.consensusCreateTopic.adminKey.ed25519 == admin_key.to_bytes_raw()
    assert schedulable_body.consensusCreateTopic.submitKey.ed25519 == submit_key.to_bytes_raw()
    assert schedulable_body.consensusCreateTopic.autoRenewAccount.accountNum == 5

# This test uses fixture mock_account_ids as parameter
def test_missing_operator_in_topic_create(mock_account_ids):
    """
    Test that building the body fails if no operator ID is set.
    """
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction(memo="No Operator")
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Operator account ID is not set."):
        tx.build_transaction_body()

def test_missing_node_in_topic_create():
    """
    Test that building the body fails if no node account ID is set.
    """
    tx = TopicCreateTransaction(memo="No Node")
    tx.operator_account_id = AccountId(0, 0, 2)

    with pytest.raises(ValueError, match="Node account ID is not set."):
        tx.build_transaction_body()

# This test uses fixtures (mock_account_ids, private_key) as parameters
def test_sign_topic_create_transaction(mock_account_ids, private_key):
    """
    Test signing the TopicCreateTransaction with a private key.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicCreateTransaction(memo="Signing test")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx._transaction_body_bytes.setdefault(node_account_id, body_bytes)

    tx.sign(private_key)
    assert len(tx._signature_map[body_bytes].sigPair) == 1

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
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS
        assert isinstance(receipt.topic_id, TopicId)
        assert receipt.topic_id.shard == 0
        assert receipt.topic_id.realm == 0
        assert receipt.topic_id.num == 123