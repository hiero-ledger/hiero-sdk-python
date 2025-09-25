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

from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def custom_fixed_fee():
    """Fixture for a CustomFixedFee object"""
    return CustomFixedFee(
        amount=1000,
        denominating_token_id=TokenId(0, 0, 500),
        fee_collector_account_id=AccountId(0, 0, 600),
    )


@pytest.fixture
def multiple_custom_fees():
    """Fixture for multiple CustomFixedFee objects"""
    return [
        CustomFixedFee(
            amount=1000,
            denominating_token_id=TokenId(0, 0, 500),
            fee_collector_account_id=AccountId(0, 0, 600),
        ),
        CustomFixedFee(
            amount=2000,
            denominating_token_id=TokenId(0, 0, 700),
            fee_collector_account_id=AccountId(0, 0, 800),
        ),
    ]


# This test uses fixture mock_account_ids as parameter
def test_build_topic_create_transaction_body(mock_account_ids, custom_fixed_fee):
    """Test building a TopicCreateTransaction body"""
    _, _, node_account_id, _, _ = mock_account_ids

    admin_key = PrivateKey.generate().public_key()
    submit_key = PrivateKey.generate().public_key()
    fee_schedule_key = PrivateKey.generate().public_key()
    fee_exempt_keys = [
        PrivateKey.generate().public_key(),
        PrivateKey.generate().public_key(),
    ]

    tx = TopicCreateTransaction(
        memo="Hello Topic",
        admin_key=admin_key,
        submit_key=submit_key,
        custom_fees=[custom_fixed_fee],
        fee_schedule_key=fee_schedule_key,
        fee_exempt_keys=fee_exempt_keys,
    )

    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()

    assert transaction_body.consensusCreateTopic.memo == "Hello Topic"
    assert (
        transaction_body.consensusCreateTopic.adminKey.ed25519
        == admin_key.to_bytes_raw()
    )
    assert (
        transaction_body.consensusCreateTopic.submitKey.ed25519
        == submit_key.to_bytes_raw()
    )
    assert len(transaction_body.consensusCreateTopic.custom_fees) == 1
    assert (
        transaction_body.consensusCreateTopic.fee_schedule_key.ed25519
        == fee_schedule_key.to_bytes_raw()
    )
    assert len(transaction_body.consensusCreateTopic.fee_exempt_key_list) == 2


def test_build_scheduled_body(mock_account_ids, custom_fixed_fee):
    """
    Test building a scheduled body for TopicCreateTransaction with valid properties.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    
    # Create private key for the admin key
    admin_key = PrivateKey.generate().public_key()
    submit_key = PrivateKey.generate().public_key()
    fee_schedule_key = PrivateKey.generate().public_key()
    fee_exempt_keys = [
        PrivateKey.generate().public_key(),
        PrivateKey.generate().public_key(),
    ]

    # Create a transaction with all fields set including new ones
    tx = TopicCreateTransaction()
    tx.set_memo("Scheduled Topic")
    tx.set_admin_key(admin_key)
    tx.set_submit_key(submit_key)
    tx.set_auto_renew_account(AccountId(0, 0, 5))
    tx.set_custom_fees([custom_fixed_fee])
    tx.set_fee_schedule_key(fee_schedule_key)
    tx.set_fee_exempt_keys(fee_exempt_keys)

    # Build the scheduled transaction body
    schedulable_body = tx.build_scheduled_body()
    
    # Verify it's the right type
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    
    # Verify the transaction was built with the topic create type
    assert schedulable_body.HasField("consensusCreateTopic")
    
    # Verify fields in the scheduled body
    assert schedulable_body.consensusCreateTopic.memo == "Scheduled Topic"
    assert (
        schedulable_body.consensusCreateTopic.adminKey.ed25519
        == admin_key.to_bytes_raw()
    )
    assert (
        schedulable_body.consensusCreateTopic.submitKey.ed25519
        == submit_key.to_bytes_raw()
    )
    assert schedulable_body.consensusCreateTopic.autoRenewAccount.accountNum == 5
    assert len(schedulable_body.consensusCreateTopic.custom_fees) == 1
    assert (
        schedulable_body.consensusCreateTopic.fee_schedule_key.ed25519
        == fee_schedule_key.to_bytes_raw()
    )
    assert len(schedulable_body.consensusCreateTopic.fee_exempt_key_list) == 2


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
    topic_id = basic_types_pb2.TopicID(shardNum=0, realmNum=0, topicNum=123)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS, topicID=topic_id
            ),
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


def test_constructor(multiple_custom_fees):
    """Test constructor with all fields."""
    admin_key = PrivateKey.generate().public_key()
    submit_key = PrivateKey.generate().public_key()
    fee_schedule_key = PrivateKey.generate().public_key()
    fee_exempt_keys = [
        PrivateKey.generate().public_key(),
        PrivateKey.generate().public_key(),
    ]

    # Test constructor with all fields
    tx = TopicCreateTransaction(
        memo="Test Topic",
        admin_key=admin_key,
        submit_key=submit_key,
        custom_fees=multiple_custom_fees,
        fee_schedule_key=fee_schedule_key,
        fee_exempt_keys=fee_exempt_keys,
    )

    assert tx.memo == "Test Topic"
    assert tx.admin_key == admin_key
    assert tx.submit_key == submit_key
    assert tx.custom_fees == multiple_custom_fees
    assert tx.fee_schedule_key == fee_schedule_key
    assert tx.fee_exempt_keys == fee_exempt_keys

    # Test constructor with default values
    tx_default = TopicCreateTransaction()
    assert tx_default.memo == ""
    assert tx_default.admin_key is None
    assert tx_default.submit_key is None
    assert tx_default.custom_fees == []
    assert tx_default.fee_schedule_key is None
    assert tx_default.fee_exempt_keys == []


def test_set_custom_fees(multiple_custom_fees):
    """Test setting custom fees for the topic creation transaction."""
    tx = TopicCreateTransaction()

    # Test setting custom fees
    result = tx.set_custom_fees(multiple_custom_fees)
    assert tx.custom_fees == multiple_custom_fees
    assert result is tx  # Method chaining

    # Test setting to empty list
    result = tx.set_custom_fees([])
    assert tx.custom_fees == []
    assert result is tx


def test_set_fee_schedule_key():
    """Test setting fee schedule key for the topic creation transaction."""
    tx = TopicCreateTransaction()
    fee_schedule_key = PrivateKey.generate().public_key()

    result = tx.set_fee_schedule_key(fee_schedule_key)
    assert tx.fee_schedule_key == fee_schedule_key
    assert result is tx  # Method chaining


def test_set_fee_exempt_keys():
    """Test setting fee exempt keys for the topic creation transaction."""
    tx = TopicCreateTransaction()
    fee_exempt_keys = [
        PrivateKey.generate().public_key(),
        PrivateKey.generate().public_key(),
    ]

    result = tx.set_fee_exempt_keys(fee_exempt_keys)
    assert tx.fee_exempt_keys == fee_exempt_keys
    assert result is tx  # Method chaining

    # Test setting to empty list
    result = tx.set_fee_exempt_keys([])
    assert tx.fee_exempt_keys == []
    assert result is tx


def test_method_chaining(custom_fixed_fee):
    """Test method chaining functionality."""
    tx = TopicCreateTransaction()
    fee_schedule_key = PrivateKey.generate().public_key()
    fee_exempt_keys = [PrivateKey.generate().public_key()]

    result = (
        tx.set_custom_fees([custom_fixed_fee])
        .set_fee_schedule_key(fee_schedule_key)
        .set_fee_exempt_keys(fee_exempt_keys)
    )

    assert result is tx
    assert tx.custom_fees == [custom_fixed_fee]
    assert tx.fee_schedule_key == fee_schedule_key
    assert tx.fee_exempt_keys == fee_exempt_keys


def test_set_methods_require_not_frozen(
    mock_account_ids, custom_fixed_fee, mock_client
):
    """Test that setter methods raise exception when transaction is frozen."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction()
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id
    tx.freeze_with(mock_client)  # Freeze the transaction

    fee_schedule_key = PrivateKey.generate().public_key()
    fee_exempt_keys = [PrivateKey.generate().public_key()]

    test_cases = [
        ("set_custom_fees", [custom_fixed_fee]),
        ("set_fee_schedule_key", fee_schedule_key),
        ("set_fee_exempt_keys", fee_exempt_keys),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(tx, method_name)(value)

