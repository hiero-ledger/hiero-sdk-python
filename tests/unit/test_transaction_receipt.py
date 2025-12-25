import pytest

from hiero_sdk_python.hapi.services import transaction_receipt_pb2
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt


pytestmark = pytest.mark.unit


def test_transaction_receipt_children_default_empty():
    proto = transaction_receipt_pb2.TransactionReceipt()
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    assert receipt.children == []


def test_transaction_receipt_set_children_updates_property():
    parent_proto = transaction_receipt_pb2.TransactionReceipt()
    child_proto_1 = transaction_receipt_pb2.TransactionReceipt()
    child_proto_2 = transaction_receipt_pb2.TransactionReceipt()

    parent = TransactionReceipt(receipt_proto=parent_proto, transaction_id=None)
    child1 = TransactionReceipt(receipt_proto=child_proto_1, transaction_id=None)
    child2 = TransactionReceipt(receipt_proto=child_proto_2, transaction_id=None)

    parent._set_children([child1, child2])

    assert len(parent.children) == 2
    assert parent.children[0] is child1
    assert parent.children[1] is child2
