"""Tests for associated registered nodes on NodeCreate/NodeUpdate transactions."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.nodes.node_create_transaction import (
    NodeCreateParams,
    NodeCreateTransaction,
)
from hiero_sdk_python.nodes.node_update_transaction import (
    NodeUpdateParams,
    NodeUpdateTransaction,
)
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit


def _freeze(tx):
    tx.transaction_id = TransactionId.generate(AccountId(0, 0, 100))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()
    return tx


# ---------------------------------------------------------------------------
# NodeCreateTransaction – associated_registered_nodes
# ---------------------------------------------------------------------------


class TestNodeCreateAssociatedRegisteredNodes:
    def test_serializes_associated_registered_nodes(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeCreateTransaction()
        tx.set_associated_registered_nodes([1, 2, 3])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert list(body.nodeCreate.associated_registered_node) == [1, 2, 3]

    def test_add_associated_registered_node_chains(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeCreateTransaction()
        result = tx.add_associated_registered_node(10)
        assert result is tx
        tx.add_associated_registered_node(20)
        assert tx.associated_registered_nodes == [10, 20]

        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert list(body.nodeCreate.associated_registered_node) == [10, 20]

    def test_set_replaces_list(self):
        tx = NodeCreateTransaction()
        tx.add_associated_registered_node(1)
        result = tx.set_associated_registered_nodes([5, 6])
        assert result is tx
        assert tx.associated_registered_nodes == [5, 6]

    def test_from_bytes_round_trip(self):
        tx = NodeCreateTransaction()
        tx.set_associated_registered_nodes([7, 8, 9])
        _freeze(tx)

        restored = Transaction.from_bytes(tx.to_bytes())
        assert isinstance(restored, NodeCreateTransaction)
        assert list(restored.associated_registered_nodes) == [7, 8, 9]

    def test_preserves_behavior_when_unset(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeCreateTransaction()
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.nodeCreate.associated_registered_node) == 0

    def test_default_empty_list(self):
        tx = NodeCreateTransaction()
        assert tx.associated_registered_nodes == []

    def test_constructor_compat_no_break(self):
        params = NodeCreateParams(account_id=AccountId(0, 0, 1))
        tx = NodeCreateTransaction(params)
        assert tx.account_id == AccountId(0, 0, 1)
        assert tx.associated_registered_nodes == []


# ---------------------------------------------------------------------------
# NodeUpdateTransaction – associated_registered_nodes
# ---------------------------------------------------------------------------


class TestNodeUpdateAssociatedRegisteredNodes:
    def test_does_not_serialize_when_none(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeUpdateTransaction()
        tx.node_id = 1
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert not body.nodeUpdate.HasField("associated_registered_node_list")

    def test_serializes_empty_when_cleared(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeUpdateTransaction()
        tx.node_id = 1
        tx.clear_associated_registered_nodes()
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.nodeUpdate.HasField("associated_registered_node_list")
        assert len(body.nodeUpdate.associated_registered_node_list.associated_registered_node) == 0

    def test_serializes_non_empty(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeUpdateTransaction()
        tx.node_id = 1
        tx.set_associated_registered_nodes([10, 20])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.nodeUpdate.HasField("associated_registered_node_list")
        assert list(body.nodeUpdate.associated_registered_node_list.associated_registered_node) == [10, 20]

    def test_add_initializes_and_appends(self):
        tx = NodeUpdateTransaction()
        assert tx.associated_registered_nodes is None
        result = tx.add_associated_registered_node(5)
        assert result is tx
        assert tx.associated_registered_nodes == [5]
        tx.add_associated_registered_node(6)
        assert tx.associated_registered_nodes == [5, 6]

    def test_set_replaces_list(self):
        tx = NodeUpdateTransaction()
        tx.add_associated_registered_node(1)
        result = tx.set_associated_registered_nodes([100, 200])
        assert result is tx
        assert tx.associated_registered_nodes == [100, 200]

    def test_from_bytes_round_trip_non_empty(self):
        tx = NodeUpdateTransaction()
        tx.node_id = 5
        tx.set_associated_registered_nodes([10, 20, 30])
        _freeze(tx)

        restored = Transaction.from_bytes(tx.to_bytes())
        assert isinstance(restored, NodeUpdateTransaction)
        assert list(restored.associated_registered_nodes) == [10, 20, 30]

    def test_from_bytes_round_trip_cleared(self):
        tx = NodeUpdateTransaction()
        tx.node_id = 5
        tx.clear_associated_registered_nodes()
        _freeze(tx)

        restored = Transaction.from_bytes(tx.to_bytes())
        assert isinstance(restored, NodeUpdateTransaction)
        assert restored.associated_registered_nodes == []

    def test_from_bytes_round_trip_unset(self):
        tx = NodeUpdateTransaction()
        tx.node_id = 5
        _freeze(tx)

        restored = Transaction.from_bytes(tx.to_bytes())
        assert isinstance(restored, NodeUpdateTransaction)
        assert restored.associated_registered_nodes is None

    def test_preserves_existing_behavior(self, mock_account_ids):
        """Existing fields still work when associated_registered_nodes is not used."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = NodeUpdateTransaction()
        tx.node_id = 1
        tx.set_description("hello")
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.nodeUpdate.description.value == "hello"
        assert not body.nodeUpdate.HasField("associated_registered_node_list")

    def test_constructor_compat_no_break(self):
        params = NodeUpdateParams(node_id=5)
        tx = NodeUpdateTransaction(params)
        assert tx.node_id == 5
        assert tx.associated_registered_nodes is None
