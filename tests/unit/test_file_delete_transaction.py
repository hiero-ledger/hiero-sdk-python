"""
Test cases for the FileDeleteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

pytestmark = pytest.mark.unit


def test_build_transaction_body(mock_account_ids, file_id):
    """Test building a file delete transaction body with a valid value."""
    account_id, _, node_account_id, _, _ = mock_account_ids
    delete_tx = FileDeleteTransaction(file_id=file_id)
    delete_tx.node_account_id = node_account_id
    delete_tx.operator_account_id = account_id

    transaction_body = delete_tx.build_transaction_body()

    assert transaction_body.fileDelete.fileID == file_id._to_proto()


def test_missing_file_id():
    """Test that building a transaction without setting FileID raises a ValueError."""
    delete_tx = FileDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required FileID"):
        delete_tx.build_transaction_body()


def test_set_file_id(file_id):
    """Test setting file_id using the setter method."""
    delete_tx = FileDeleteTransaction()

    result = delete_tx.set_file_id(file_id)

    assert delete_tx.file_id == file_id
    assert result == delete_tx  # Should return self for method chaining


def test_constructor_with_file_id(file_id):
    """Test constructor with file_id parameter."""
    delete_tx = FileDeleteTransaction(file_id=file_id)

    assert delete_tx.file_id == file_id


def test_constructor_without_file_id():
    """Test constructor without file_id parameter."""
    delete_tx = FileDeleteTransaction()

    assert delete_tx.file_id is None


def test_sign_transaction(mock_client, file_id):
    """Test signing the file delete transaction with a private key."""
    delete_tx = FileDeleteTransaction(file_id=file_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)

    delete_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = delete_tx._transaction_body_bytes[node_id]

    assert len(delete_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = delete_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, file_id):
    """Test converting the file delete transaction to protobuf format after signing."""

    delete_tx = FileDeleteTransaction(file_id=file_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)

    delete_tx.sign(private_key)
    proto = delete_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_build_scheduled_body(mock_account_ids, file_id):
    """Test building a schedulable file delete transaction body."""
    account_id, _, node_account_id, _, _ = mock_account_ids
    delete_tx = FileDeleteTransaction(file_id=file_id)
    delete_tx.node_account_id = node_account_id
    delete_tx.operator_account_id = account_id

    # Build the scheduled body
    schedulable_body = delete_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with file delete type
    assert schedulable_body.HasField("fileDelete")

    # Verify fields in the schedulable body
    assert schedulable_body.fileDelete.fileID == file_id._to_proto()

def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    delete_tx = FileDeleteTransaction()

    mock_channel = MagicMock()
    mock_file_stub = MagicMock()
    mock_channel.file = mock_file_stub

    method = delete_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_file_stub.deleteFile
