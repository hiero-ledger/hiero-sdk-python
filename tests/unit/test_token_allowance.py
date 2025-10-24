"""
Unit tests for the TokenAllowance class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    TokenAllowance as TokenAllowanceProto,
)
from hiero_sdk_python.tokens.token_allowance import TokenAllowance
from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit


@pytest.fixture
def token_allowance():
    """Fixture for a TokenAllowance object"""
    return TokenAllowance(
        token_id=TokenId(0, 0, 100),
        owner_account_id=AccountId(0, 0, 200),
        spender_account_id=AccountId(0, 0, 300),
        amount=1000,
    )


@pytest.fixture
def proto_token_allowance():
    """Fixture for a proto TokenAllowance object"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)

    proto = TokenAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        amount=1000,
    )
    return proto


def test_token_allowance_initialization(token_allowance):
    """Test the initialization of the TokenAllowance class"""
    assert token_allowance.token_id == TokenId(0, 0, 100)
    assert token_allowance.owner_account_id == AccountId(0, 0, 200)
    assert token_allowance.spender_account_id == AccountId(0, 0, 300)
    assert token_allowance.amount == 1000


def test_token_allowance_default_initialization():
    """Test the default initialization of the TokenAllowance class"""
    allowance = TokenAllowance()
    assert allowance.token_id is None
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None
    assert allowance.amount == 0


def test_token_allowance_with_custom_amount():
    """Test TokenAllowance initialization with custom amount"""
    allowance = TokenAllowance(
        token_id=TokenId(0, 0, 100),
        amount=5000,
    )
    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.amount == 5000
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None


def test_from_proto(proto_token_allowance):
    """Test the from_proto method of the TokenAllowance class"""
    allowance = TokenAllowance._from_proto(proto_token_allowance)

    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.amount == 1000


def test_from_proto_with_minimal_fields():
    """Test the from_proto method with minimal fields"""
    proto = TokenAllowanceProto(amount=2500)

    allowance = TokenAllowance._from_proto(proto)
    assert allowance.token_id is None
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None
    assert allowance.amount == 2500


def test_from_proto_none_raises_error():
    """Test the from_proto method with a None proto"""
    with pytest.raises(ValueError, match="TokenAllowance proto is None"):
        TokenAllowance._from_proto(None)


def test_to_proto(token_allowance):
    """Test the to_proto method of the TokenAllowance class"""
    proto = token_allowance._to_proto()

    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.owner == AccountId(0, 0, 200)._to_proto()
    assert proto.spender == AccountId(0, 0, 300)._to_proto()
    assert proto.amount == 1000


def test_to_proto_with_none_values():
    """Test the to_proto method with none values"""
    allowance = TokenAllowance()
    proto = allowance._to_proto()

    # Protobuf fields are not None when unset, but HasField returns False
    assert not proto.HasField("tokenId")
    assert not proto.HasField("owner")
    assert not proto.HasField("spender")
    assert proto.amount == 0


def test_to_proto_with_zero_amount():
    """Test the to_proto method with zero amount"""
    allowance = TokenAllowance(
        token_id=TokenId(0, 0, 100),
        amount=0,
    )
    proto = allowance._to_proto()

    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.amount == 0


def test_proto_conversion_full_object(token_allowance):
    """Test proto conversion with fully populated object"""
    converted = TokenAllowance._from_proto(token_allowance._to_proto())

    assert converted.token_id == token_allowance.token_id
    assert converted.owner_account_id == token_allowance.owner_account_id
    assert converted.spender_account_id == token_allowance.spender_account_id
    assert converted.amount == token_allowance.amount


def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    allowance = TokenAllowance(
        token_id=TokenId(0, 0, 100),
        amount=1500,
    )
    converted = TokenAllowance._from_proto(allowance._to_proto())

    assert converted.token_id == allowance.token_id
    assert converted.amount == allowance.amount
    assert converted.owner_account_id is None
    assert converted.spender_account_id is None


def test_proto_conversion_with_different_values():
    """Test proto conversion with different values"""
    allowance = TokenAllowance(
        token_id=TokenId(1, 2, 3),
        owner_account_id=AccountId(4, 5, 6),
        spender_account_id=AccountId(7, 8, 9),
        amount=9999,
    )
    converted = TokenAllowance._from_proto(allowance._to_proto())

    assert converted.token_id == TokenId(1, 2, 3)
    assert converted.owner_account_id == AccountId(4, 5, 6)
    assert converted.spender_account_id == AccountId(7, 8, 9)
    assert converted.amount == 9999


def test_string_representation(token_allowance):
    """Test the string representation of TokenAllowance"""
    str_repr = str(token_allowance)

    assert "TokenAllowance(" in str_repr
    assert "owner_account_id=0.0.200" in str_repr
    assert "spender_account_id=0.0.300" in str_repr
    assert "token_id=0.0.100" in str_repr
    assert "amount=1000" in str_repr


def test_string_representation_with_none_values():
    """Test the string representation with None values"""
    allowance = TokenAllowance()
    str_repr = str(allowance)

    assert "TokenAllowance(" in str_repr
    assert "owner_account_id=None" in str_repr
    assert "spender_account_id=None" in str_repr
    assert "token_id=None" in str_repr
    assert "amount=0" in str_repr


def test_string_representation_with_zero_amount():
    """Test the string representation with zero amount"""
    allowance = TokenAllowance(
        token_id=TokenId(0, 0, 100),
        amount=0,
    )
    str_repr = str(allowance)

    assert "amount=0" in str_repr


def test_repr_method(token_allowance):
    """Test the repr method returns the same as str"""
    assert repr(token_allowance) == str(token_allowance)


def test_from_proto_field_helper():
    """Test the _from_proto_field helper method"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)

    proto = TokenAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        amount=3000,
    )

    # Test with populated field
    result = TokenAllowance._from_proto_field(proto, "tokenId", TokenId._from_proto)
    assert result == token_id

    # Test with populated field
    result = TokenAllowance._from_proto_field(proto, "owner", AccountId._from_proto)
    assert result == owner_account_id

    # Test with empty field
    result = TokenAllowance._from_proto_field(proto, "spender", AccountId._from_proto)
    assert result is None


def test_amount_edge_cases():
    """Test amount with various edge cases"""
    # Test with large amount
    allowance = TokenAllowance(amount=999999999)
    assert allowance.amount == 999999999

    # Test with negative amount
    allowance = TokenAllowance(amount=-1000)
    assert allowance.amount == -1000

    # Test with zero amount
    allowance = TokenAllowance(amount=0)
    assert allowance.amount == 0


def test_proto_conversion_edge_cases():
    """Test proto conversion with edge case amounts"""
    # Test with large amount
    allowance = TokenAllowance(amount=999999999)
    converted = TokenAllowance._from_proto(allowance._to_proto())
    assert converted.amount == 999999999

    # Test with negative amount
    allowance = TokenAllowance(amount=-1000)
    converted = TokenAllowance._from_proto(allowance._to_proto())
    assert converted.amount == -1000


def test_proto_conversion_with_partial_fields():
    """Test proto conversion with only some fields set"""
    allowance = TokenAllowance(
        token_id=TokenId(0, 0, 100),
        spender_account_id=AccountId(0, 0, 300),
        amount=2000,
    )
    converted = TokenAllowance._from_proto(allowance._to_proto())

    assert converted.token_id == TokenId(0, 0, 100)
    assert converted.spender_account_id == AccountId(0, 0, 300)
    assert converted.amount == 2000
    assert converted.owner_account_id is None
