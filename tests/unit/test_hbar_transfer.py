"""
Unit tests for the HbarTransfer class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.hbar_transfer import HbarTransfer

pytestmark = pytest.mark.unit


def test_hbar_transfer_constructor(mock_account_ids):
    """Test the HbarTransfer constructor with various parameters"""
    account_id, _, _, _, _ = mock_account_ids
    amount = 1000
    hbar_transfer = HbarTransfer()
    assert hbar_transfer.account_id is None
    assert hbar_transfer.amount is None
    assert hbar_transfer.is_approved is False

    hbar_transfer = HbarTransfer(account_id=account_id, amount=amount)

    # Verify all fields were set correctly
    assert hbar_transfer.account_id == account_id
    assert hbar_transfer.amount == amount
    assert hbar_transfer.is_approved is False

    # Test with explicit is_approved=True
    approved_transfer = HbarTransfer(account_id=account_id, amount=amount, is_approved=True)

    assert approved_transfer.account_id == account_id
    assert approved_transfer.amount == amount
    assert approved_transfer.is_approved is True


def test_from_proto_none():
    """Test converting a None protobuf object to a HbarTransfer"""
    proto = None
    with pytest.raises(ValueError, match="HbarTransfer proto is None"):
        HbarTransfer._from_proto(proto)


def test_to_proto(mock_account_ids):
    """Test converting HbarTransfer to a protobuf object"""
    account_id, _, _, _, _ = mock_account_ids
    amount = 1000
    is_approved = True

    hbar_transfer = HbarTransfer(account_id=account_id, amount=amount, is_approved=is_approved)

    # Convert to protobuf
    proto = hbar_transfer._to_proto()

    # Verify protobuf fields
    assert proto.accountID.shardNum == account_id.shard
    assert proto.accountID.realmNum == account_id.realm
    assert proto.accountID.accountNum == account_id.num

    assert proto.amount == amount
    assert proto.is_approval is is_approved


def test_from_proto(mock_account_ids):
    """Test converting a protobuf object to a HbarTransfer"""
    account_id, _, _, _, _ = mock_account_ids
    amount = 1000
    is_approved = True

    proto = basic_types_pb2.AccountAmount(
        accountID=account_id._to_proto(), amount=amount, is_approval=is_approved
    )

    hbar_transfer = HbarTransfer._from_proto(proto)

    assert hbar_transfer.account_id == account_id
    assert hbar_transfer.amount == amount
    assert hbar_transfer.is_approved == is_approved


def test_from_proto_empty():
    """Test converting an empty protobuf object to a HbarTransfer"""
    proto = basic_types_pb2.AccountAmount()

    hbar_transfer = HbarTransfer._from_proto(proto)

    assert hbar_transfer.account_id == AccountId()
    assert hbar_transfer.amount == 0
    assert hbar_transfer.is_approved is False


def test_str_representation(mock_account_ids):
    """Test string representation of HbarTransfer"""
    account_id, _, _, _, _ = mock_account_ids
    amount = 1000

    hbar_transfer = HbarTransfer(account_id=account_id, amount=amount, is_approved=True)

    str_repr = str(hbar_transfer)
    assert "HbarTransfer(" in str_repr
    assert f"account_id={account_id}" in str_repr
    assert f"amount={amount}" in str_repr
    assert "is_approved=True" in str_repr
