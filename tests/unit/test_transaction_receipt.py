import pytest

from hiero_sdk_python.account.account_id import AccountId
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


# --- account_id property tests (regression coverage for #1849) ---


def test_account_id_returns_none_when_not_set():
    """account_id is None when accountID field is absent."""
    proto = transaction_receipt_pb2.TransactionReceipt()
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    assert hasattr(receipt, "account_id"), "TransactionReceipt must expose account_id"
    assert receipt.account_id is None


def test_account_id_returns_account_with_nonzero_num():
    """account_id is parsed correctly when accountNum is a normal nonzero number."""
    account_proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234)
    proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    assert hasattr(receipt, "account_id"), "TransactionReceipt must expose account_id"
    account_id = receipt.account_id
    assert account_id is not None, "account_id must not be None when accountID is set with a nonzero accountNum"
    assert isinstance(account_id, AccountId), f"account_id must be an AccountId, got {type(account_id)}"
    assert account_id.shard == 0, f"Expected shard=0, got {account_id.shard}"
    assert account_id.realm == 0, f"Expected realm=0, got {account_id.realm}"
    assert account_id.num == 1234, f"Expected num=1234, got {account_id.num}"


def test_account_id_returns_account_with_alias_and_zero_num():
    """
    account_id is returned when accountNum is 0 but an EVM alias is set.

    Regression test for issue #1849: auto-account creation from an EVM address
    produces a child receipt where the accountID field is set but accountNum
    may be 0 while the alias carries the identity. The previous guard
    ``accountNum != 0`` incorrectly dropped these valid accounts.
    """
    evm_alias = bytes.fromhex("f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14")
    account_proto = basic_types_pb2.AccountID(
        shardNum=0, realmNum=0, accountNum=0, alias=evm_alias
    )
    proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    receipt = TransactionReceipt(receipt_proto=proto, transaction_id=None)

    assert hasattr(receipt, "account_id"), "TransactionReceipt must expose account_id"
    account_id = receipt.account_id
    assert account_id is not None, (
        "account_id must not be None for an auto-created account "
        "with accountNum=0 and an EVM alias"
    )
    assert isinstance(account_id, AccountId), f"account_id must be an AccountId, got {type(account_id)}"
    assert account_id.shard == 0, f"Expected shard=0, got {account_id.shard}"
    assert account_id.realm == 0, f"Expected realm=0, got {account_id.realm}"
    assert account_id.num == 0, f"Expected num=0, got {account_id.num}"
    assert account_id.evm_address is not None, "evm_address must be populated from the proto alias"
    assert account_id.evm_address.to_string() == "f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14", (
        f"Unexpected evm_address: {account_id.evm_address.to_string()}"
    )


def test_account_id_in_child_receipt():
    """
    account_id is accessible from a child receipt with a regular accountNum.

    Ensures TransactionGetReceiptQuery with include_children=True correctly
    exposes account_id on child receipts for accounts with nonzero accountNum.
    """
    account_proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=5678)
    child_proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    parent_proto = transaction_receipt_pb2.TransactionReceipt()

    parent = TransactionReceipt(receipt_proto=parent_proto, transaction_id=None)
    child = TransactionReceipt(receipt_proto=child_proto, transaction_id=None)
    parent._set_children([child])

    assert len(parent.children) == 1, "Expected 1 child receipt"
    created_account_id = parent.children[0].account_id
    assert created_account_id is not None, "account_id must not be None in a child receipt with accountNum set"
    assert isinstance(created_account_id, AccountId), f"account_id must be an AccountId, got {type(created_account_id)}"
    assert created_account_id.num == 5678, f"Expected num=5678, got {created_account_id.num}"


def test_account_id_in_child_receipt_with_alias_regression():
    """
    account_id with alias+accountNum=0 is accessible from a child receipt.

    This is the exact failing scenario from issue #1849: a TransferTransaction
    to an EVM address creates an account automatically; the resulting child
    receipt has accountNum=0 with the EVM alias — the previous guard would
    have silently dropped it, returning None.
    """
    evm_alias = bytes.fromhex("f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14")
    account_proto = basic_types_pb2.AccountID(
        shardNum=0, realmNum=0, accountNum=0, alias=evm_alias
    )
    child_proto = transaction_receipt_pb2.TransactionReceipt(accountID=account_proto)
    parent_proto = transaction_receipt_pb2.TransactionReceipt()

    parent = TransactionReceipt(receipt_proto=parent_proto, transaction_id=None)
    child = TransactionReceipt(receipt_proto=child_proto, transaction_id=None)
    parent._set_children([child])

    assert len(parent.children) == 1, "Expected 1 child receipt"
    created_account_id = parent.children[0].account_id
    assert created_account_id is not None, (
        "account_id must not be None in a child receipt for an auto-created "
        "EVM alias account (accountNum=0) — regression for issue #1849"
    )
    assert isinstance(created_account_id, AccountId), f"account_id must be an AccountId, got {type(created_account_id)}"
    assert created_account_id.num == 0, f"Expected num=0 for alias account, got {created_account_id.num}"
    assert created_account_id.evm_address is not None, "evm_address must be set for alias-based child receipt"
    assert created_account_id.evm_address.to_string() == "f7aaff1e0a3ca62a82ebdcffa6c19345f14b5e14"
