"""Unit tests for RegisteredNodeDeleteTransaction."""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.transaction.transaction import Transaction

pytestmark = pytest.mark.unit


def test_constructor_with_parameter():
    """The constructor should populate the registered node id."""
    transaction = RegisteredNodeDeleteTransaction(registered_node_id=9)

    assert transaction.registered_node_id == 9


def test_constructor_default_values():
    """Default construction should produce an unset id."""
    transaction = RegisteredNodeDeleteTransaction()

    assert transaction.registered_node_id is None


def test_build_transaction_body(mock_account_ids):
    """Building a transaction body should populate the registered-node oneof."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeDeleteTransaction(registered_node_id=9)
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    transaction_body = transaction.build_transaction_body()

    assert transaction_body.HasField("registeredNodeDelete")
    assert transaction_body.registeredNodeDelete.registered_node_id == 9


def test_build_scheduled_body():
    """Registered node delete transactions should be schedulable."""
    transaction = RegisteredNodeDeleteTransaction(registered_node_id=9)

    scheduled_body = transaction.build_scheduled_body()

    assert isinstance(scheduled_body, SchedulableTransactionBody)
    assert scheduled_body.HasField("registeredNodeDelete")


def test_build_transaction_body_requires_registered_node_id(mock_account_ids):
    """A registered node id must be provided for deletes."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeDeleteTransaction()
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required RegisteredNodeID"):
        transaction.build_transaction_body()


def test_get_method():
    """The transaction should use the registered-node delete RPC."""
    transaction = RegisteredNodeDeleteTransaction()
    channel = MagicMock()
    channel.address_book = MagicMock()

    method = transaction._get_method(channel)

    assert method.query is None
    assert method.transaction == channel.address_book.deleteRegisteredNode


def test_from_bytes_restores_registered_node_delete_transaction(mock_client):
    """Transaction.from_bytes should restore the registered-node delete type."""
    transaction = RegisteredNodeDeleteTransaction(registered_node_id=9)
    transaction.freeze_with(mock_client)

    restored = Transaction.from_bytes(transaction.to_bytes())

    assert isinstance(restored, RegisteredNodeDeleteTransaction)
    assert restored.registered_node_id == 9
