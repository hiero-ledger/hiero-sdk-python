from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.query.query import Query


def test_set_single_node_account_id():
    q = Query()
    node = AccountId(0, 0, 3)

    # Test deprecated for backward compatiblity
    q.set_node_account_id(node)

    assert q.node_account_ids == [node]


def test_set_single_node_account_id_using_setter():
    q = Query()
    node = AccountId(0, 0, 3)

    # Test deprecated for backward compatiblity
    q.node_account_id = node

    assert q.node_account_ids == [node]


def test_get_single_node_account_id():
    q = Query()
    node = AccountId(0, 0, 3)

    q.set_node_account_ids([node])

    # Test deprecated for backward compatiblity
    assert q.node_account_id == node


def test_set_multiple_node_account_ids():
    q = Query()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    q.set_node_account_ids(nodes)

    assert q.node_account_ids == nodes


def test_set_multiple_node_account_ids_using_setters():
    q = Query()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    q.node_account_ids = nodes

    assert q.node_account_ids == nodes


def test_node_account_id_advance_method():
    q = Query()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    q.set_node_account_ids(nodes)

    assert q._node_account_ids.index == 0
    assert q._node_account_ids.current == nodes[0]

    index = q._node_account_ids.advance()
    assert index == 0  # returns current index
    assert q._node_account_ids.index == 1
    assert q._node_account_ids.current == nodes[1]
