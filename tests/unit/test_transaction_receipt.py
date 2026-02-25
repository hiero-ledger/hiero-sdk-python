import pytest

from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_receipt_pb2
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


# --- account_id property tests ---

def test_account_id_returns_none_when_not_set():
    """account_id is None when accountID field is absent."""
    proto = transaction_receipt_pb2.TransactionReceipt()
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    assert receipt.account_id is None


def test_account_id_returns_account_with_nonzero_num():
    """account_id is parsed correctly when accountNum is a normal nonzero number."""
    account_proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234)
    proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    account_id = receipt.account_id
    assert account_id is not None
    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 1234


def test_account_id_returns_account_with_alias_and_zero_num():
    """
    account_id is returned when accountNum is 0 but an alias is set.

    Regression test for issue #1849: auto-account creation from an EVM address
    produces a child receipt where the accountID field is set but accountNum
    may be 0 while the alias carries the identity. The previous guard
    ``accountNum != 0`` incorrectly dropped these valid accounts.
    """
    # Simulate an EVM alias (20 bytes)
    evm_alias = bytes.fromhex("f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14")
    account_proto = basic_types_pb2.AccountID(
        shardNum=0, realmNum=0, accountNum=0, alias=evm_alias
    )
    proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    account_id = receipt.account_id
    assert account_id is not None, (
        "account_id must not be None for an auto-created account "
        "with accountNum=0 and an EVM alias"
    )
    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.evm_address is not None
    assert account_id.evm_address.to_string() == "f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14"


def test_account_id_in_child_receipt():
    """
    account_id is accessible from a child receipt.

    Regression test for issue #1849: TransactionGetReceiptQuery with
    include_children=True should expose account_id from child receipts.
    """
    account_proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=5678)
    child_proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    parent_proto = transaction_receipt_pb2.TransactionReceipt()

    parent = TransactionReceipt(receipt_proto=parent_proto, transaction_id=None)
    child = TransactionReceipt(receipt_proto=child_proto, transaction_id=None)
    parent._set_children([child])

    assert len(parent.children) == 1
    created_account_id = parent.children[0].account_id
    assert created_account_id is not None
    assert created_account_id.num == 5678
