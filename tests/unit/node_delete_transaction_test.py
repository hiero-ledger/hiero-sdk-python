"""
Test cases for the NodeDeleteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction

pytestmark = pytest.mark.unit


@pytest.fixture
def node_id():
    """Fixture for node ID."""
    return 5


def test_constructor_with_parameter(node_id):
    """Test creating a node delete transaction with constructor parameter."""
    node_tx = NodeDeleteTransaction(node_id=node_id)

    assert node_tx.node_id == node_id


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    node_tx = NodeDeleteTransaction()

    assert node_tx.node_id is None


def test_build_transaction_body(mock_account_ids, node_id):
    """Test building a node delete transaction body."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    node_tx = NodeDeleteTransaction(node_id=node_id)

    # Set operator and node account IDs needed for building transaction body
    node_tx.operator_account_id = operator_id
    node_tx.node_account_id = node_account_id

    transaction_body = node_tx.build_transaction_body()

    # Verify the transaction body contains nodeDelete field
    assert transaction_body.HasField("nodeDelete")

    # Verify the node ID is correctly set
    node_delete = transaction_body.nodeDelete
    assert node_delete.node_id == node_id


def test_build_transaction_body_missing_node_id(mock_account_ids):
    """Test building a transaction body when node_id is not set raises ValueError."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    node_tx = NodeDeleteTransaction()

    # Set operator and node account IDs needed for building transaction body
    node_tx.operator_account_id = operator_id
    node_tx.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required NodeID"):
        node_tx.build_transaction_body()


def test_build_scheduled_body(node_id):
    """Test building a schedulable node delete transaction body."""
    node_tx = NodeDeleteTransaction(node_id=node_id)

    schedulable_body = node_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with node delete type
    assert schedulable_body.HasField("nodeDelete")

    # Verify the node ID is correctly set
    node_delete = schedulable_body.nodeDelete
    assert node_delete.node_id == node_id


def test_build_scheduled_body_missing_node_id():
    """Test building a scheduled body when node_id is not set raises ValueError."""
    node_tx = NodeDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required NodeID"):
        node_tx.build_scheduled_body()


def test_set_node_id(node_id):
    """Test setting node_id using the setter method."""
    node_tx = NodeDeleteTransaction()

    result = node_tx.set_node_id(node_id)

    assert node_tx.node_id == node_id
    assert result is node_tx  # Should return self for method chaining


def test_set_node_id_none():
    """Test setting node_id to None using the setter method."""
    node_tx = NodeDeleteTransaction()

    result = node_tx.set_node_id(None)

    assert node_tx.node_id is None
    assert result is node_tx  # Should return self for method chaining


def test_set_node_id_requires_not_frozen(mock_client, node_id):
    """Test that set_node_id raises exception when transaction is frozen."""
    node_tx = NodeDeleteTransaction(node_id=node_id)
    node_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        node_tx.set_node_id(node_id)


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    node_tx = NodeDeleteTransaction()

    mock_channel = MagicMock()
    mock_address_book_stub = MagicMock()
    mock_channel.address_book = mock_address_book_stub

    method = node_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_address_book_stub.deleteNode


def test_sign_transaction(mock_client, node_id):
    """Test signing the node delete transaction with a private key."""
    node_tx = NodeDeleteTransaction(node_id=node_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    node_tx.freeze_with(mock_client)
    node_tx.sign(private_key)

    node_id_key = mock_client.network.current_node._account_id
    body_bytes = node_tx._transaction_body_bytes[node_id_key]

    assert len(node_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = node_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, node_id):
    """Test converting the node delete transaction to protobuf format after signing."""
    node_tx = NodeDeleteTransaction(node_id=node_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    node_tx.freeze_with(mock_client)
    node_tx.sign(private_key)
    proto = node_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_build_proto_body(node_id):
    """Test building the protobuf body directly."""
    node_tx = NodeDeleteTransaction(node_id=node_id)

    proto_body = node_tx._build_proto_body()

    assert proto_body.node_id == node_id


def test_build_proto_body_missing_node_id():
    """Test building the protobuf body when node_id is not set raises ValueError."""
    node_tx = NodeDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required NodeID"):
        node_tx._build_proto_body()
