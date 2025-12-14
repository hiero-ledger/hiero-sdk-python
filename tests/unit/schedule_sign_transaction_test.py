"""
Test cases for the ScheduleSignTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_sign_transaction import ScheduleSignTransaction

pytestmark = pytest.mark.unit


@pytest.fixture
def schedule_id():
    """Fixture to provide a mock ScheduleId instance."""
    return ScheduleId(shard=0, realm=0, schedule=123)


def test_constructor_with_schedule_id(schedule_id):
    """Test creating a schedule sign transaction with constructor parameter."""
    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)

    assert schedule_sign_tx.schedule_id == schedule_id
    assert schedule_sign_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    schedule_sign_tx = ScheduleSignTransaction()

    assert schedule_sign_tx.schedule_id is None
    assert schedule_sign_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_set_schedule_id(schedule_id):
    """Test setting schedule_id using the setter method."""
    schedule_sign_tx = ScheduleSignTransaction()

    result = schedule_sign_tx.set_schedule_id(schedule_id)

    assert schedule_sign_tx.schedule_id == schedule_id
    assert result is schedule_sign_tx  # Should return self for method chaining


def test_set_schedule_id_to_none(schedule_id):
    """Test setting schedule_id to None using the setter method."""
    schedule_sign_tx = ScheduleSignTransaction()
    schedule_sign_tx.schedule_id = schedule_id  # Set initial value

    result = schedule_sign_tx.set_schedule_id(None)

    assert schedule_sign_tx.schedule_id is None
    assert result is schedule_sign_tx  # Should return self for method chaining


def test_set_schedule_id_requires_not_frozen(mock_client, schedule_id):
    """Test that set_schedule_id raises exception when transaction is frozen."""
    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)
    schedule_sign_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        schedule_sign_tx.set_schedule_id(schedule_id)


def test_build_proto_body_with_schedule_id(schedule_id):
    """Test building protobuf body with a valid schedule ID."""
    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)

    proto_body = schedule_sign_tx._build_proto_body()

    assert proto_body.scheduleID == schedule_id._to_proto()


def test_build_proto_body_without_schedule_id_raises_error():
    """Test building protobuf body without a schedule ID."""
    schedule_sign_tx = ScheduleSignTransaction()

    with pytest.raises(ValueError, match="Missing required ScheduleID"):
        schedule_sign_tx._build_proto_body()


def test_build_transaction_body_with_valid_schedule_id(mock_account_ids, schedule_id):
    """Test building a schedule sign transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)

    # Set operator and node account IDs needed for building transaction body
    schedule_sign_tx.operator_account_id = operator_id
    schedule_sign_tx.node_account_id = node_account_id

    transaction_body = schedule_sign_tx.build_transaction_body()

    # Verify the transaction body contains scheduleSign field
    assert transaction_body.HasField("scheduleSign")

    # Verify the schedule ID is correctly set
    schedule_sign = transaction_body.scheduleSign
    assert schedule_sign.scheduleID == schedule_id._to_proto()


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    schedule_sign_tx = ScheduleSignTransaction()

    mock_channel = MagicMock()
    mock_schedule_stub = MagicMock()
    mock_channel.schedule = mock_schedule_stub

    method = schedule_sign_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_schedule_stub.signSchedule


def test_sign_transaction(mock_client, schedule_id):
    """Test signing the schedule sign transaction with a private key."""
    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    schedule_sign_tx.freeze_with(mock_client)
    schedule_sign_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = schedule_sign_tx._transaction_body_bytes[node_id]

    assert len(schedule_sign_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = schedule_sign_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, schedule_id):
    """Test converting the schedule sign transaction to protobuf format after signing."""
    schedule_sign_tx = ScheduleSignTransaction(schedule_id=schedule_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    schedule_sign_tx.freeze_with(mock_client)
    schedule_sign_tx.sign(private_key)
    proto = schedule_sign_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_method_chaining():
    """Test that setter methods support method chaining."""
    schedule_sign_tx = ScheduleSignTransaction()
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    result = schedule_sign_tx.set_schedule_id(schedule_id)

    assert result is schedule_sign_tx
    assert schedule_sign_tx.schedule_id == schedule_id


def test_build_scheduled_body_raises_exception():
    """Test that build_scheduled_body raises ValueError."""
    schedule_sign_tx = ScheduleSignTransaction()

    with pytest.raises(ValueError, match="Cannot schedule a ScheduleSignTransaction"):
        schedule_sign_tx.build_scheduled_body()


def test_default_transaction_fee():
    """Test that the default transaction fee is set correctly."""
    schedule_sign_tx = ScheduleSignTransaction()

    assert schedule_sign_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_schedule_id_property_access():
    """Test that schedule_id property can be accessed and modified."""
    schedule_sign_tx = ScheduleSignTransaction()
    schedule_id = ScheduleId(shard=5, realm=10, schedule=15)

    # Test setting via property
    schedule_sign_tx.schedule_id = schedule_id
    assert schedule_sign_tx.schedule_id == schedule_id

    # Test getting via property
    retrieved_schedule_id = schedule_sign_tx.schedule_id
    assert retrieved_schedule_id == schedule_id
