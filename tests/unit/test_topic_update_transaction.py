"""Tests for the TopicUpdateTransaction functionality."""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
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

from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixtures (mock_account_ids, topic_id) as parameters
def test_build_topic_update_transaction_body(mock_account_ids, topic_id):
    """Test building a TopicUpdateTransaction body with valid topic ID and memo."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicUpdateTransaction(topic_id=topic_id, memo="Updated Memo")

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()
    assert transaction_body.consensusUpdateTopic.topicID.topicNum == 1234
    assert transaction_body.consensusUpdateTopic.memo.value == "Updated Memo"
    
# This test uses fixtures (topic_id) as parameters
def test_build_scheduled_body(topic_id):
    """Test building a schedulable TopicUpdateTransaction body with all fields."""
    # Generate keys and create an account ID for testing
    admin_key = PrivateKey.generate().public_key()
    submit_key = PrivateKey.generate().public_key()
    auto_renew_account = AccountId(0, 0, 9876)
    
    # Create transaction with all available fields
    tx = TopicUpdateTransaction()
    tx.set_topic_id(topic_id)
    tx.set_memo("Scheduled Topic Update")
    tx.set_admin_key(admin_key)
    tx.set_submit_key(submit_key)
    tx.set_auto_renew_period(Duration(8000000))  # Custom duration
    tx.set_auto_renew_account(auto_renew_account)
    tx.set_fee_exempt_keys([admin_key])
    tx.set_fee_schedule_key(admin_key)
    tx.set_custom_fees([CustomFixedFee(1000, fee_collector_account_id=AccountId(0, 0, 9876))])
    
    # Build the scheduled body
    schedulable_body = tx.build_scheduled_body()
    
    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    
    # Verify the transaction was built with topic update type
    assert schedulable_body.HasField("consensusUpdateTopic")
    
    # Verify all fields in the scheduled body
    assert schedulable_body.consensusUpdateTopic.topicID.topicNum == 1234
    assert schedulable_body.consensusUpdateTopic.memo.value == "Scheduled Topic Update"
    assert schedulable_body.consensusUpdateTopic.adminKey.ed25519 == admin_key.to_bytes_raw()
    assert schedulable_body.consensusUpdateTopic.submitKey.ed25519 == submit_key.to_bytes_raw()
    assert schedulable_body.consensusUpdateTopic.autoRenewPeriod.seconds == 8000000
    assert schedulable_body.consensusUpdateTopic.autoRenewAccount.accountNum == 9876
    assert (
        schedulable_body.consensusUpdateTopic.fee_exempt_key_list.keys[0].ed25519
        == admin_key.to_bytes_raw()
    )
    assert (
        schedulable_body.consensusUpdateTopic.fee_schedule_key.ed25519
        == admin_key.to_bytes_raw()
    )
    assert (
        schedulable_body.consensusUpdateTopic.custom_fees.fees[0].fixed_fee.amount
        == 1000
    )
    assert (
        schedulable_body.consensusUpdateTopic.custom_fees.fees[
            0
        ].fee_collector_account_id.accountNum
        == 9876
    )


# This test uses fixture mock_account_ids as parameter
def test_missing_topic_id_in_update(mock_account_ids):
    """Test that building fails if no topic ID is provided."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicUpdateTransaction(topic_id=None, memo="No ID")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required fields"):
        tx.build_transaction_body()


# This test uses fixtures (mock_account_ids, topic_id, private_key) as parameters
def test_sign_topic_update_transaction(mock_account_ids, topic_id, private_key):
    """Test signing the TopicUpdateTransaction with a private key."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicUpdateTransaction(topic_id=topic_id, memo="Signature test")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx._transaction_body_bytes.setdefault(node_account_id, body_bytes)

    tx.sign(private_key)
    assert len(tx._signature_map[body_bytes].sigPair) == 1


# This test uses fixture topic_id as parameter
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
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS


# This test uses fixture topic_id as parameter
def test_topic_update_transaction_with_all_fields(topic_id):
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
        fee_collector_account_id = AccountId(0, 0, 9876)
        custom_fee = CustomFixedFee(1000, fee_collector_account_id=fee_collector_account_id)
        
        tx = (
            TopicUpdateTransaction()
            .set_topic_id(topic_id)
            .set_memo("Comprehensive update")
            .set_admin_key(admin_key)
            .set_submit_key(submit_key)
            .set_auto_renew_period(Duration(7776000))  # 90 days
            .set_auto_renew_account(auto_renew_account)
            .set_custom_fees([custom_fee])
            .set_fee_schedule_key(admin_key)
            .set_fee_exempt_keys([admin_key])
        )
        
        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS
