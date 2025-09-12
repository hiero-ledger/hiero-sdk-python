"""
Test cases for the FreezeTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.freeze_type_pb2 import (
    FreezeType as proto_FreezeType,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.system.freeze_type import FreezeType
from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


@pytest.fixture
def freeze_params():
    """Fixture for freeze transaction parameters."""
    return {
        "start_time": Timestamp(1640995200, 0),
        "file_id": FileId(0, 0, 123),
        "file_hash": b"test-file-hash",
        "freeze_type": FreezeType.FREEZE_ONLY,
    }


def test_constructor_with_parameters(freeze_params):
    """Test creating a freeze transaction with constructor parameters."""
    freeze_tx = FreezeTransaction(
        start_time=freeze_params["start_time"],
        file_id=freeze_params["file_id"],
        file_hash=freeze_params["file_hash"],
        freeze_type=freeze_params["freeze_type"],
    )

    assert freeze_tx.start_time == freeze_params["start_time"]
    assert freeze_tx.file_id == freeze_params["file_id"]
    assert freeze_tx.file_hash == freeze_params["file_hash"]
    assert freeze_tx.freeze_type == freeze_params["freeze_type"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    freeze_tx = FreezeTransaction()

    assert freeze_tx.start_time is None
    assert freeze_tx.file_id is None
    assert freeze_tx.file_hash is None
    assert freeze_tx.freeze_type is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, freeze_params):
    """Test building a freeze transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    freeze_tx = FreezeTransaction(
        start_time=freeze_params["start_time"],
        file_id=freeze_params["file_id"],
        file_hash=freeze_params["file_hash"],
        freeze_type=freeze_params["freeze_type"],
    )

    # Set operator and node account IDs needed for building transaction body
    freeze_tx.operator_account_id = operator_id
    freeze_tx.node_account_id = node_account_id

    transaction_body = freeze_tx.build_transaction_body()

    # Verify the transaction body contains freeze field
    assert transaction_body.HasField("freeze")

    # Verify all fields are correctly set
    freeze_body = transaction_body.freeze
    assert freeze_body.start_time == freeze_params["start_time"]._to_protobuf()
    assert freeze_body.update_file == freeze_params["file_id"]._to_proto()
    assert freeze_body.file_hash == freeze_params["file_hash"]
    assert freeze_body.freeze_type == freeze_params["freeze_type"]._to_proto()


def test_build_transaction_body_with_none_values(mock_account_ids):
    """Test building a freeze transaction body with None values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    freeze_tx = FreezeTransaction()

    # Set operator and node account IDs needed for building transaction body
    freeze_tx.operator_account_id = operator_id
    freeze_tx.node_account_id = node_account_id

    transaction_body = freeze_tx.build_transaction_body()

    # Verify the transaction body contains freeze field
    assert transaction_body.HasField("freeze")

    # Verify all fields are None or default values
    freeze_body = transaction_body.freeze
    assert not freeze_body.HasField("start_time")  # Empty protobuf object when None
    assert not freeze_body.HasField("update_file")  # Empty protobuf object when None
    assert freeze_body.file_hash == b""  # Empty bytes when None
    assert freeze_body.freeze_type == proto_FreezeType.UNKNOWN_FREEZE_TYPE


def test_build_scheduled_body(freeze_params):
    """Test building a schedulable freeze transaction body."""
    freeze_tx = FreezeTransaction(
        start_time=freeze_params["start_time"],
        file_id=freeze_params["file_id"],
        file_hash=freeze_params["file_hash"],
        freeze_type=freeze_params["freeze_type"],
    )

    schedulable_body = freeze_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with freeze type
    assert schedulable_body.HasField("freeze")

    # Verify fields in the schedulable body
    freeze_body = schedulable_body.freeze
    assert freeze_body.start_time == freeze_params["start_time"]._to_protobuf()
    assert freeze_body.update_file == freeze_params["file_id"]._to_proto()
    assert freeze_body.file_hash == freeze_params["file_hash"]
    assert freeze_body.freeze_type == freeze_params["freeze_type"]._to_proto()


def test_set_start_time(freeze_params):
    """Test setting start_time using the setter method."""
    freeze_tx = FreezeTransaction()

    result = freeze_tx.set_start_time(freeze_params["start_time"])

    assert freeze_tx.start_time == freeze_params["start_time"]
    assert result is freeze_tx  # Should return self for method chaining


def test_set_file_id(freeze_params):
    """Test setting file_id using the setter method."""
    freeze_tx = FreezeTransaction()

    result = freeze_tx.set_file_id(freeze_params["file_id"])

    assert freeze_tx.file_id == freeze_params["file_id"]
    assert result is freeze_tx  # Should return self for method chaining


def test_set_file_hash(freeze_params):
    """Test setting file_hash using the setter method."""
    freeze_tx = FreezeTransaction()

    result = freeze_tx.set_file_hash(freeze_params["file_hash"])

    assert freeze_tx.file_hash == freeze_params["file_hash"]
    assert result is freeze_tx  # Should return self for method chaining


def test_set_freeze_type(freeze_params):
    """Test setting freeze_type using the setter method."""
    freeze_tx = FreezeTransaction()

    result = freeze_tx.set_freeze_type(freeze_params["freeze_type"])

    assert freeze_tx.freeze_type == freeze_params["freeze_type"]
    assert result is freeze_tx  # Should return self for method chaining


def test_method_chaining_with_all_setters(freeze_params):
    """Test that all setter methods support method chaining."""
    freeze_tx = FreezeTransaction()

    result = (
        freeze_tx.set_start_time(freeze_params["start_time"])
        .set_file_id(freeze_params["file_id"])
        .set_file_hash(freeze_params["file_hash"])
        .set_freeze_type(freeze_params["freeze_type"])
    )

    assert result is freeze_tx
    assert freeze_tx.start_time == freeze_params["start_time"]
    assert freeze_tx.file_id == freeze_params["file_id"]
    assert freeze_tx.file_hash == freeze_params["file_hash"]
    assert freeze_tx.freeze_type == freeze_params["freeze_type"]


def test_set_methods_require_not_frozen(mock_client, freeze_params):
    """Test that setter methods raise exception when transaction is frozen."""
    freeze_tx = FreezeTransaction()
    freeze_tx.freeze_with(mock_client)

    test_cases = [
        ("set_start_time", freeze_params["start_time"]),
        ("set_file_id", freeze_params["file_id"]),
        ("set_file_hash", freeze_params["file_hash"]),
        ("set_freeze_type", freeze_params["freeze_type"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(freeze_tx, method_name)(value)


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    freeze_tx = FreezeTransaction()

    mock_channel = MagicMock()
    mock_freeze_stub = MagicMock()
    mock_channel.freeze = mock_freeze_stub

    method = freeze_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_freeze_stub.freeze


def test_sign_transaction(mock_client):
    """Test signing the freeze transaction with a private key."""
    freeze_tx = FreezeTransaction()
    freeze_tx.set_freeze_type(FreezeType.FREEZE_ONLY)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    freeze_tx.freeze_with(mock_client)
    freeze_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = freeze_tx._transaction_body_bytes[node_id]

    assert len(freeze_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = freeze_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client):
    """Test converting the freeze transaction to protobuf format after signing."""
    freeze_tx = FreezeTransaction()
    freeze_tx.set_freeze_type(FreezeType.FREEZE_ONLY)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    freeze_tx.freeze_with(mock_client)
    freeze_tx.sign(private_key)
    proto = freeze_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_build_proto_body_with_all_fields(freeze_params):
    """Test building protobuf body with all fields set."""
    freeze_tx = FreezeTransaction(
        start_time=freeze_params["start_time"],
        file_id=freeze_params["file_id"],
        file_hash=freeze_params["file_hash"],
        freeze_type=freeze_params["freeze_type"],
    )

    proto_body = freeze_tx._build_proto_body()

    assert proto_body.start_time == freeze_params["start_time"]._to_protobuf()
    assert proto_body.update_file == freeze_params["file_id"]._to_proto()
    assert proto_body.file_hash == freeze_params["file_hash"]
    assert proto_body.freeze_type == freeze_params["freeze_type"]._to_proto()


def test_build_proto_body_with_none_fields():
    """Test building protobuf body with None fields."""
    freeze_tx = FreezeTransaction()

    proto_body = freeze_tx._build_proto_body()

    assert not proto_body.HasField("start_time")
    assert not proto_body.HasField("update_file")
    assert proto_body.file_hash == b""
    assert proto_body.freeze_type == proto_FreezeType.UNKNOWN_FREEZE_TYPE
