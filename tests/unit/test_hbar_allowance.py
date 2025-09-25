"""
Unit tests for the HbarAllowance class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    CryptoAllowance as CryptoAllowanceProto,
)
from hiero_sdk_python.tokens.hbar_allowance import HbarAllowance

pytestmark = pytest.mark.unit


@pytest.fixture
def hbar_allowance():
    """Fixture for a HbarAllowance object"""
    return HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        spender_account_id=AccountId(0, 0, 300),
        amount=1000,
    )


@pytest.fixture
def proto_hbar_allowance():
    """Fixture for a proto HbarAllowance object"""
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)

    proto = CryptoAllowanceProto(
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        amount=1000,
    )
    return proto


def test_hbar_allowance_initialization(hbar_allowance):
    """Test the initialization of the HbarAllowance class"""
    assert hbar_allowance.owner_account_id == AccountId(0, 0, 200)
    assert hbar_allowance.spender_account_id == AccountId(0, 0, 300)
    assert hbar_allowance.amount == 1000


def test_hbar_allowance_default_initialization():
    """Test the default initialization of the HbarAllowance class"""
    allowance = HbarAllowance()
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None
    assert allowance.amount == 0


def test_hbar_allowance_with_custom_amount():
    """Test HbarAllowance initialization with custom amount"""
    allowance = HbarAllowance(amount=5000)
    assert allowance.amount == 5000
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None


def test_hbar_allowance_with_only_owner():
    """Test HbarAllowance initialization with only owner"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        amount=2500,
    )
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.amount == 2500
    assert allowance.spender_account_id is None


def test_hbar_allowance_with_only_spender():
    """Test HbarAllowance initialization with only spender"""
    allowance = HbarAllowance(
        spender_account_id=AccountId(0, 0, 300),
        amount=3000,
    )
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.amount == 3000
    assert allowance.owner_account_id is None


def test_from_proto(proto_hbar_allowance):
    """Test the from_proto method of the HbarAllowance class"""
    allowance = HbarAllowance._from_proto(proto_hbar_allowance)

    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.amount == 1000


def test_from_proto_with_minimal_fields():
    """Test the from_proto method with minimal fields"""
    proto = CryptoAllowanceProto(amount=2500)

    allowance = HbarAllowance._from_proto(proto)
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None
    assert allowance.amount == 2500


def test_from_proto_with_only_owner():
    """Test the from_proto method with only owner"""
    owner_account_id = AccountId(0, 0, 200)
    proto = CryptoAllowanceProto(
        owner=owner_account_id._to_proto(),
        amount=1500,
    )

    allowance = HbarAllowance._from_proto(proto)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id is None
    assert allowance.amount == 1500


def test_from_proto_with_only_spender():
    """Test the from_proto method with only spender"""
    spender_account_id = AccountId(0, 0, 300)
    proto = CryptoAllowanceProto(
        spender=spender_account_id._to_proto(),
        amount=2000,
    )

    allowance = HbarAllowance._from_proto(proto)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.owner_account_id is None
    assert allowance.amount == 2000


def test_from_proto_none_raises_error():
    """Test the from_proto method with a None proto"""
    with pytest.raises(ValueError, match="HbarAllowance proto is None"):
        HbarAllowance._from_proto(None)


def test_to_proto(hbar_allowance):
    """Test the to_proto method of the HbarAllowance class"""
    proto = hbar_allowance._to_proto()

    assert proto.owner == AccountId(0, 0, 200)._to_proto()
    assert proto.spender == AccountId(0, 0, 300)._to_proto()
    assert proto.amount == 1000


def test_to_proto_with_none_values():
    """Test the to_proto method with none values"""
    allowance = HbarAllowance()
    proto = allowance._to_proto()

    # Protobuf fields are not None when unset, but HasField returns False
    assert not proto.HasField("owner")
    assert not proto.HasField("spender")
    assert proto.amount == 0


def test_to_proto_with_zero_amount():
    """Test the to_proto method with zero amount"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        amount=0,
    )
    proto = allowance._to_proto()

    assert proto.owner == AccountId(0, 0, 200)._to_proto()
    assert proto.amount == 0


def test_proto_conversion_full_object(hbar_allowance):
    """Test proto conversion with fully populated object"""
    converted = HbarAllowance._from_proto(hbar_allowance._to_proto())

    assert converted.owner_account_id == hbar_allowance.owner_account_id
    assert converted.spender_account_id == hbar_allowance.spender_account_id
    assert converted.amount == hbar_allowance.amount


def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    allowance = HbarAllowance(amount=1500)
    converted = HbarAllowance._from_proto(allowance._to_proto())

    assert converted.amount == allowance.amount
    assert converted.owner_account_id is None
    assert converted.spender_account_id is None


def test_proto_conversion_with_different_values():
    """Test proto conversion with different values"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(1, 2, 3),
        spender_account_id=AccountId(4, 5, 6),
        amount=9999,
    )
    converted = HbarAllowance._from_proto(allowance._to_proto())

    assert converted.owner_account_id == AccountId(1, 2, 3)
    assert converted.spender_account_id == AccountId(4, 5, 6)
    assert converted.amount == 9999


def test_string_representation_full_object(hbar_allowance):
    """Test the string representation with full object"""
    str_repr = str(hbar_allowance)

    assert "HbarAllowance(" in str_repr
    assert "owner_account_id=0.0.200" in str_repr
    assert "spender_account_id=0.0.300" in str_repr
    assert "amount=1000" in str_repr


def test_string_representation_with_none_values():
    """Test the string representation with None values"""
    allowance = HbarAllowance()
    str_repr = str(allowance)

    assert "HbarAllowance(" in str_repr
    assert "amount=0" in str_repr
    assert "owner_account_id" not in str_repr
    assert "spender_account_id" not in str_repr


def test_string_representation_with_only_owner():
    """Test the string representation with only owner"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        amount=2500,
    )
    str_repr = str(allowance)

    assert "HbarAllowance(" in str_repr
    assert "owner_account_id=0.0.200" in str_repr
    assert "amount=2500" in str_repr
    assert "spender_account_id" not in str_repr


def test_string_representation_with_only_spender():
    """Test the string representation with only spender"""
    allowance = HbarAllowance(
        spender_account_id=AccountId(0, 0, 300),
        amount=3000,
    )
    str_repr = str(allowance)

    assert "HbarAllowance(" in str_repr
    assert "spender_account_id=0.0.300" in str_repr
    assert "amount=3000" in str_repr
    assert "owner_account_id" not in str_repr


def test_string_representation_with_zero_amount():
    """Test the string representation with zero amount"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        spender_account_id=AccountId(0, 0, 300),
        amount=0,
    )
    str_repr = str(allowance)

    assert "amount=0" in str_repr


def test_repr_method(hbar_allowance):
    """Test the repr method returns the same as str"""
    assert repr(hbar_allowance) == str(hbar_allowance)


def test_from_proto_field_helper():
    """Test the _from_proto_field helper method"""
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)

    proto = CryptoAllowanceProto(
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        amount=3000,
    )

    # Test with populated field
    result = HbarAllowance._from_proto_field(proto, "owner", AccountId._from_proto)
    assert result == owner_account_id

    # Test with populated field
    result = HbarAllowance._from_proto_field(proto, "spender", AccountId._from_proto)
    assert result == spender_account_id

    # Test with empty field (should not happen in this proto, but testing the method)
    proto_empty = CryptoAllowanceProto(amount=1000)
    result = HbarAllowance._from_proto_field(proto_empty, "owner", AccountId._from_proto)
    assert result is None


def test_amount_edge_cases():
    """Test amount with various edge cases"""
    # Test with large amount
    allowance = HbarAllowance(amount=999999999)
    assert allowance.amount == 999999999

    # Test with negative amount
    allowance = HbarAllowance(amount=-1000)
    assert allowance.amount == -1000

    # Test with zero amount
    allowance = HbarAllowance(amount=0)
    assert allowance.amount == 0


def test_proto_conversion_edge_cases():
    """Test proto conversion with edge case amounts"""
    # Test with large amount
    allowance = HbarAllowance(amount=999999999)
    converted = HbarAllowance._from_proto(allowance._to_proto())
    assert converted.amount == 999999999

    # Test with negative amount
    allowance = HbarAllowance(amount=-1000)
    converted = HbarAllowance._from_proto(allowance._to_proto())
    assert converted.amount == -1000


def test_proto_conversion_with_partial_fields():
    """Test proto conversion with only some fields set"""
    allowance = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        amount=2000,
    )
    converted = HbarAllowance._from_proto(allowance._to_proto())

    assert converted.owner_account_id == AccountId(0, 0, 200)
    assert converted.amount == 2000
    assert converted.spender_account_id is None


def test_string_representation_conditional_formatting():
    """Test that string representation changes based on available fields"""
    # Full object
    allowance_full = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        spender_account_id=AccountId(0, 0, 300),
        amount=1000,
    )
    str_full = str(allowance_full)
    assert "owner_account_id" in str_full and "spender_account_id" in str_full

    # Only owner
    allowance_owner = HbarAllowance(
        owner_account_id=AccountId(0, 0, 200),
        amount=1000,
    )
    str_owner = str(allowance_owner)
    assert "owner_account_id" in str_owner and "spender_account_id" not in str_owner

    # Only spender
    allowance_spender = HbarAllowance(
        spender_account_id=AccountId(0, 0, 300),
        amount=1000,
    )
    str_spender = str(allowance_spender)
    assert "spender_account_id" in str_spender and "owner_account_id" not in str_spender

    # Only amount
    allowance_amount = HbarAllowance(amount=1000)
    str_amount = str(allowance_amount)
    assert (
        "amount=1000" in str_amount
        and "owner_account_id" not in str_amount
        and "spender_account_id" not in str_amount
    )
