import pytest
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.account.account_id import AccountId


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

    txn.set_node_account_id(node)

    assert txn.node_account_ids == [node]
    assert txn._used_node_account_id is None


def test_set_multiple_node_account_ids():
    txn = DummyTransaction()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    txn.set_node_account_ids(nodes)

    assert txn.node_account_ids == nodes
    assert txn._used_node_account_id is None


def test_select_node_account_id():
    txn = DummyTransaction()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    txn.set_node_account_ids(nodes)

    selected = txn._select_node_account_id()

    assert selected == nodes[0]
    assert txn._used_node_account_id == nodes[0]
