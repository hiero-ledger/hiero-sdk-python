"""Tests for the TopicDeleteTransaction functionality."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def _round_trip(tx, signed=False):
    tx.set_transaction_id(TransactionId.from_string("0.0.2@1700000000.123"))
    tx.set_node_account_ids([AccountId(0, 0, 3), AccountId(0, 0, 4)])
    tx.set_transaction_memo("Outer transaction memo")
    tx.transaction_fee = 12345678
    tx.freeze()

    if signed:
        tx.sign(PrivateKey.generate_ed25519())

    encoded = tx.to_bytes()
    restored = Transaction.from_bytes(encoded)

    assert type(restored) is type(tx)
    assert restored.memo == tx.memo
    assert restored.transaction_id == tx.transaction_id
    assert restored.transaction_fee == tx.transaction_fee
    assert restored._transaction_body_bytes == tx._transaction_body_bytes
    assert restored._signature_map == tx._signature_map
    assert restored.to_bytes() == encoded
    return restored


# This test uses fixtures (mock_account_ids, topic_id) as parameters
def test_build_topic_delete_transaction_body(mock_account_ids, topic_id):
    """Test building a TopicDeleteTransaction body with a valid topic ID."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicDeleteTransaction(topic_id=topic_id)

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.set_node_account_ids([node_account_id])

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
    tx.set_node_account_ids([node_account_id])

    with pytest.raises(ValueError, match="Missing required fields"):
        tx.build_transaction_body()


# This test uses fixtures (mock_account_ids, topic_id, private_key) as parameters
def test_sign_topic_delete_transaction(mock_account_ids, topic_id, private_key):
    """Test signing the TopicDeleteTransaction with a private key."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction_id = TransactionId.generate(operator_id)

    tx = TopicDeleteTransaction(topic_id=topic_id)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.set_node_account_ids([node_account_id])
    tx.set_transaction_id(transaction_id)

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx._transaction_body_bytes.setdefault(transaction_id, dict(node_account_id=body_bytes))

    tx.sign(private_key)
    assert len(tx._signature_map[body_bytes].sigPair) == 1


# This test uses fixture topic_id as parameter
def test_execute_topic_delete_transaction(topic_id):
    """Test executing the TopicDeleteTransaction successfully with mock server."""
    # Create success response for the transaction submission
    tx_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    # Create receipt response with SUCCESS status
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        )
    )

    response_sequences = [
        [tx_response, receipt_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        tx = TopicDeleteTransaction().set_topic_id(topic_id)

        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")

        # Verify the receipt contains the expected values
        assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.parametrize("topic_id", [TopicId(), TopicId(7, 8, 900)])
@pytest.mark.parametrize("signed", [False, True])
def test_from_bytes_restores_topic_id(topic_id, signed):
    tx = TopicDeleteTransaction(topic_id=topic_id)
    restored = _round_trip(tx, signed)

    assert restored.topic_id == tx.topic_id


def test_from_protobuf_preserves_absent_topic_id():
    body = transaction_pb2.TransactionBody()
    body.consensusDeleteTopic.SetInParent()

    restored = TopicDeleteTransaction._from_protobuf(body)

    assert restored.topic_id is None
