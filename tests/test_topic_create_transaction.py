import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    transaction_receipt_pb2
)
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.hapi.services import timestamp_pb2 as hapi_timestamp_pb2

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

def test_sign_topic_create_transaction(mock_account_ids):
    """
    Test signing the TopicCreateTransaction with a private key.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    tx = TopicCreateTransaction(memo="Signing test")
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    private_key = PrivateKey.generate()

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx.transaction_body_bytes = body_bytes

    tx.sign(private_key)
    assert len(tx.signature_map.sigPair) == 1

def test_execute_topic_create_transaction(mock_account_ids):
    """
    Test executing the TopicCreateTransaction with a mock Client.
    """
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction(memo="Execute test")
    tx.operator_account_id = AccountId(0, 0, 2)

    client = MagicMock(spec=Client)
    client.operator_private_key = PrivateKey.generate()
    client.operator_account_id = AccountId(0, 0, 2)
    client.node_account_id = node_account_id
    client.max_attempts = 10
    
    real_tx_id = TransactionId(
        account_id=AccountId(0, 0, 2),
        valid_start=hapi_timestamp_pb2.Timestamp(seconds=11111, nanos=222)
    )
    client.generate_transaction_id.return_value = real_tx_id

    client.topic_stub = MagicMock()

    mock_response = MagicMock()
    mock_response.nodeTransactionPrecheckCode = ResponseCode.OK
    client.topic_stub.createTopic.return_value = mock_response

    proto_receipt = transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.OK)
    real_receipt = TransactionReceipt.from_proto(proto_receipt)
    client.get_transaction_receipt.return_value = real_receipt

    client.channel = MagicMock()
    
    mock_response = MagicMock()
    mock_response.transaction_id = real_tx_id
    mock_response.get_receipt.return_value = real_receipt
    
    tx._execute = MagicMock(return_value=mock_response)

    receipt = tx.execute(client)

    tx._execute.assert_called_once_with(client)
    
    assert receipt is not None
    assert receipt.status == ResponseCode.OK
    assert receipt is real_receipt
    print("Test passed: TopicCreateTransaction executed successfully.")
