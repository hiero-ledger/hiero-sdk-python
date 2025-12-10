import pytest
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.account.account_id import AccountId

def test_set_single_node_account_id():
    q = Query()
    node = AccountId(0, 0, 3)

    q.set_node_account_id(node)

    assert q.node_account_ids == [node]
    assert q._used_node_account_id is None  # not selected until execution

def test_set_multiple_node_account_ids():
    q = Query()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    q.set_node_account_ids(nodes)

    assert q.node_account_ids == nodes
    assert q._used_node_account_id is None

def test_select_node_account_id():
    q = Query()
    nodes = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    q.set_node_account_ids(nodes)

    selected = q._select_node_account_id()

    assert selected == nodes[0]
    assert q._used_node_account_id == nodes[0]
