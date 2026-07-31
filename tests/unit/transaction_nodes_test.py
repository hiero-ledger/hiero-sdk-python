from __future__ import annotations

import re

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction import Transaction


class DummyTransaction(Transaction):
    """
    Minimal subclass of Transaction for testing.
    Transaction is abstract (requires build methods), so we stub them out.
    """

    def __init__(self):
        super().__init__()

    def build_base_transaction_body(self):
        return None  # stub

    def _make_request(self):
        return None  # stub

    def _get_method(self):
        return None  # stub


def test_set_single_node_account_id():
    txn = DummyTransaction()
    node = AccountId(0, 0, 3)

    # Test deprecated for backward compatiblity
    with pytest.warns(
        DeprecationWarning,
        match=re.escape("Method 'set_node_account_id()' is deprecated; use 'set_node_account_ids()' instead."),
    ):
        txn.set_node_account_id(node)

    assert txn.node_account_ids == [node]


def test_set_single_node_account_id_using_setter():
    txn = DummyTransaction()
    node = AccountId(0, 0, 3)

    # Test deprecated for backward compatiblity
    with pytest.warns(DeprecationWarning, match="'node_account_id' is deprecated"):
        txn.node_account_id = node

    assert txn.node_account_ids == [node]


def test_get_single_node_account_id():
    txn = DummyTransaction()
    node = AccountId(0, 0, 3)

    txn.set_node_account_ids([node])

    # Test deprecated for backward compatiblity
    with pytest.warns(DeprecationWarning, match="'node_account_id' is deprecated"):
        assert txn.node_account_id == node


def test_set_multiple_node_account_ids():
    txn = DummyTransaction()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    txn.set_node_account_ids(nodes)

    assert txn.node_account_ids == nodes


def test_set_multiple_node_account_ids_using_setters():
    txn = DummyTransaction()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    txn.node_account_ids = nodes

    assert txn.node_account_ids == nodes


def test_node_account_ids_advance_method():
    txn = DummyTransaction()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    txn.set_node_account_ids(nodes)

    assert txn._node_account_ids.index == 0
    assert txn._node_account_ids.current == nodes[0]

    index = txn._node_account_ids.advance()
    assert index == 0  # returns current index
    assert txn._node_account_ids.index == 1
    assert txn._node_account_ids.current == nodes[1]
