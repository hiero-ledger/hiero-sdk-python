"""Tests for the TopicCreateTransaction functionality."""

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
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


# Helper functions for key generation and verification
def create_key(key_type, use_private):
    """
    Create a key based on type and whether to use private or public.
    
    Args:
        key_type: "ed25519" or "ecdsa"
        use_private: True for PrivateKey, False for PublicKey
    
    Returns:
        The created key (PrivateKey or PublicKey)
    """
    if key_type == "ed25519":
        private_key = PrivateKey.generate_ed25519()
    else:  # ecdsa
        private_key = PrivateKey.generate("ecdsa")
    
    return private_key if use_private else private_key.public_key()


def get_expected_public_key(key):
    """
    Get the public key from either PrivateKey or PublicKey.
    
    Args:
        key: PrivateKey or PublicKey
    
    Returns:
        PublicKey
    """
    return key if isinstance(key, PublicKey) else key.public_key()


def verify_key_in_proto(proto_key, expected_public_key, key_type):
    """
    Verify the proto key matches expected public key.
    
    Args:
        proto_key: The proto key from the transaction body
        expected_public_key: The expected PublicKey
        key_type: "ed25519" or "ecdsa"
    """
    if key_type == "ed25519":
        assert proto_key.ed25519 == expected_public_key.to_bytes_raw()
    else:  # ecdsa
        assert proto_key.HasField("ECDSA_secp256k1")
        assert proto_key.ECDSA_secp256k1 == expected_public_key.to_bytes_raw()


# This test uses fixture mock_account_ids as parameter
@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_build_topic_create_transaction_body(mock_account_ids, custom_fixed_fee, key_type, use_private):
    """Test building a TopicCreateTransaction body with different key types."""
    _, _, node_account_id, _, _ = mock_account_ids

    admin_key = create_key(key_type, use_private)
    submit_key = create_key(key_type, use_private)
    fee_schedule_key = create_key(key_type, use_private)
    fee_exempt_keys = [
        create_key(key_type, use_private),
        create_key(key_type, use_private),
    ]

    expected_admin_public = get_expected_public_key(admin_key)
    expected_submit_public = get_expected_public_key(submit_key)
    expected_fee_schedule_public = get_expected_public_key(fee_schedule_key)
    expected_fee_exempt_publics = [get_expected_public_key(key) for key in fee_exempt_keys]

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
    verify_key_in_proto(transaction_body.consensusCreateTopic.adminKey, expected_admin_public, key_type)
    verify_key_in_proto(transaction_body.consensusCreateTopic.submitKey, expected_submit_public, key_type)
    assert len(transaction_body.consensusCreateTopic.custom_fees) == 1
    verify_key_in_proto(transaction_body.consensusCreateTopic.fee_schedule_key, expected_fee_schedule_public, key_type)
    assert len(transaction_body.consensusCreateTopic.fee_exempt_key_list) == 2
    verify_key_in_proto(transaction_body.consensusCreateTopic.fee_exempt_key_list[0], expected_fee_exempt_publics[0], key_type)
    verify_key_in_proto(transaction_body.consensusCreateTopic.fee_exempt_key_list[1], expected_fee_exempt_publics[1], key_type)


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_build_scheduled_body(mock_account_ids, custom_fixed_fee, key_type, use_private):
    """
    Test building a scheduled body for TopicCreateTransaction with valid properties.
    """
    _, _, node_account_id, _, _ = mock_account_ids
    
    admin_key = create_key(key_type, use_private)
    submit_key = create_key(key_type, use_private)
    fee_schedule_key = create_key(key_type, use_private)
    fee_exempt_keys = [
        create_key(key_type, use_private),
        create_key(key_type, use_private),
    ]

    expected_admin_public = get_expected_public_key(admin_key)
    expected_submit_public = get_expected_public_key(submit_key)
    expected_fee_schedule_public = get_expected_public_key(fee_schedule_key)
    expected_fee_exempt_publics = [get_expected_public_key(key) for key in fee_exempt_keys]

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
    verify_key_in_proto(schedulable_body.consensusCreateTopic.adminKey, expected_admin_public, key_type)
    verify_key_in_proto(schedulable_body.consensusCreateTopic.submitKey, expected_submit_public, key_type)
    assert schedulable_body.consensusCreateTopic.autoRenewAccount.accountNum == 5
    assert len(schedulable_body.consensusCreateTopic.custom_fees) == 1
    verify_key_in_proto(schedulable_body.consensusCreateTopic.fee_schedule_key, expected_fee_schedule_public, key_type)
    assert len(schedulable_body.consensusCreateTopic.fee_exempt_key_list) == 2
    verify_key_in_proto(schedulable_body.consensusCreateTopic.fee_exempt_key_list[0], expected_fee_exempt_publics[0], key_type)
    verify_key_in_proto(schedulable_body.consensusCreateTopic.fee_exempt_key_list[1], expected_fee_exempt_publics[1], key_type)


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
        # Use PublicKey for this test to match original behavior
        admin_key = PrivateKey.generate_ed25519().public_key()
        tx = (
            TopicCreateTransaction()
            .set_memo("Execute test with mock server")
            .set_admin_key(admin_key)
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


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_constructor(multiple_custom_fees, key_type, use_private):
    """Test constructor with all fields using different key types."""
    admin_key = create_key(key_type, use_private)
    submit_key = create_key(key_type, use_private)
    fee_schedule_key = create_key(key_type, use_private)
    fee_exempt_keys = [
        create_key(key_type, use_private),
        create_key(key_type, use_private),
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


def test_constructor_default_values():
    """Test constructor with default values."""
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


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_set_fee_schedule_key(key_type, use_private):
    """Test setting fee schedule key for the topic creation transaction."""
    tx = TopicCreateTransaction()
    fee_schedule_key = create_key(key_type, use_private)

    result = tx.set_fee_schedule_key(fee_schedule_key)
    assert tx.fee_schedule_key == fee_schedule_key
    assert result is tx  # Method chaining


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_set_fee_exempt_keys(key_type, use_private):
    """Test setting fee exempt keys for the topic creation transaction."""
    tx = TopicCreateTransaction()
    fee_exempt_keys = [
        create_key(key_type, use_private),
        create_key(key_type, use_private),
    ]

    result = tx.set_fee_exempt_keys(fee_exempt_keys)
    assert tx.fee_exempt_keys == fee_exempt_keys
    assert result is tx  # Method chaining

    # Test setting to empty list (not parametrized, runs once)
    if key_type == "ed25519" and not use_private:  # Only run once
        tx2 = TopicCreateTransaction()
        result = tx2.set_fee_exempt_keys([])
        assert tx2.fee_exempt_keys == []
        assert result is tx2


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_method_chaining(custom_fixed_fee, key_type, use_private):
    """Test method chaining functionality."""
    tx = TopicCreateTransaction()
    fee_schedule_key = create_key(key_type, use_private)
    fee_exempt_keys = [create_key(key_type, use_private)]

    result = (
        tx.set_custom_fees([custom_fixed_fee])
        .set_fee_schedule_key(fee_schedule_key)
        .set_fee_exempt_keys(fee_exempt_keys)
    )

    assert result is tx
    assert tx.custom_fees == [custom_fixed_fee]
    assert tx.fee_schedule_key == fee_schedule_key
    assert tx.fee_exempt_keys == fee_exempt_keys


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_set_methods_require_not_frozen(
    mock_account_ids, custom_fixed_fee, mock_client, key_type, use_private
):
    """Test that setter methods raise exception when transaction is frozen."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = TopicCreateTransaction()
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id
    tx.freeze_with(mock_client)  # Freeze the transaction

    fee_schedule_key = create_key(key_type, use_private)
    fee_exempt_keys = [create_key(key_type, use_private)]

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


# Tests for PrivateKey and PublicKey support (ED25519 and ECDSA)
@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
@pytest.mark.parametrize("field_name,setter_name,proto_path", [
    ("admin_key", "set_admin_key", "adminKey"),
    ("submit_key", "set_submit_key", "submitKey"),
    ("fee_schedule_key", "set_fee_schedule_key", "fee_schedule_key"),
])
def test_single_key_fields(mock_account_ids, key_type, use_private, field_name, setter_name, proto_path):
    """Test single key fields (admin_key, submit_key, fee_schedule_key) with different key types."""
    _, _, node_account_id, _, _ = mock_account_ids
    
    # Create the key
    key = create_key(key_type, use_private)
    expected_public_key = get_expected_public_key(key)
    
    # Create transaction and set the key
    tx = TopicCreateTransaction()
    getattr(tx, setter_name)(key)
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id
    
    # Build transaction body
    transaction_body = tx.build_transaction_body()
    
    # Get the proto key from the transaction body
    proto_key = getattr(transaction_body.consensusCreateTopic, proto_path)
    
    # Verify the proto key matches the expected public key
    verify_key_in_proto(proto_key, expected_public_key, key_type)


@pytest.mark.parametrize("key_type,use_private", [
    ("ed25519", True),
    ("ed25519", False),
    ("ecdsa", True),
    ("ecdsa", False),
])
def test_fee_exempt_keys(mock_account_ids, key_type, use_private):
    """Test fee_exempt_keys list with different key types."""
    _, _, node_account_id, _, _ = mock_account_ids
    
    # Create two keys
    key1 = create_key(key_type, use_private)
    key2 = create_key(key_type, use_private)
    expected_public_key1 = get_expected_public_key(key1)
    expected_public_key2 = get_expected_public_key(key2)
    
    # Create transaction and set the keys
    tx = TopicCreateTransaction()
    tx.set_fee_exempt_keys([key1, key2])
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id
    
    # Build transaction body
    transaction_body = tx.build_transaction_body()
    
    # Verify the proto keys match the expected public keys
    fee_exempt_key_list = transaction_body.consensusCreateTopic.fee_exempt_key_list
    assert len(fee_exempt_key_list) == 2
    verify_key_in_proto(fee_exempt_key_list[0], expected_public_key1, key_type)
    verify_key_in_proto(fee_exempt_key_list[1], expected_public_key2, key_type)


def test_mixed_key_types_in_constructor(mock_account_ids):
    """Test constructor with mixed PrivateKey and PublicKey types."""
    _, _, node_account_id, _, _ = mock_account_ids
    
    ed25519_private = PrivateKey.generate_ed25519()
    ed25519_public = PrivateKey.generate_ed25519().public_key()
    ecdsa_private = PrivateKey.generate("ecdsa")
    ecdsa_public = PrivateKey.generate("ecdsa").public_key()
    
    tx = TopicCreateTransaction(
        admin_key=ed25519_private,
        submit_key=ed25519_public,
        fee_schedule_key=ecdsa_private,
        fee_exempt_keys=[ecdsa_public, ed25519_private]
    )
    tx.operator_account_id = AccountId(0, 0, 2)
    tx.node_account_id = node_account_id
    
    transaction_body = tx.build_transaction_body()
    
    # Verify all keys are correctly converted
    assert transaction_body.consensusCreateTopic.adminKey.ed25519 == ed25519_private.public_key().to_bytes_raw()
    assert transaction_body.consensusCreateTopic.submitKey.ed25519 == ed25519_public.to_bytes_raw()
    assert transaction_body.consensusCreateTopic.fee_schedule_key.HasField("ECDSA_secp256k1")
    assert len(transaction_body.consensusCreateTopic.fee_exempt_key_list) == 2

