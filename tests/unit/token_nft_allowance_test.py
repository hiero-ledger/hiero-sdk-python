"""
Unit tests for the TokenNftAllowance class.
"""

import pytest
from google.protobuf.wrappers_pb2 import BoolValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    NftAllowance as NftAllowanceProto,
)
from hiero_sdk_python.hapi.services.crypto_delete_allowance_pb2 import (
    NftRemoveAllowance as NftRemoveAllowanceProto,
)
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_allowance import TokenNftAllowance

pytestmark = pytest.mark.unit


@pytest.fixture
def token_nft_allowance():
    """Fixture for a TokenNftAllowance object"""
    return TokenNftAllowance(
        token_id=TokenId(0, 0, 100),
        owner_account_id=AccountId(0, 0, 200),
        spender_account_id=AccountId(0, 0, 300),
        serial_numbers=[1, 2, 3],
        approved_for_all=True,
        delegating_spender=AccountId(0, 0, 400),
    )


@pytest.fixture
def proto_nft_allowance():
    """Fixture for a proto NftAllowance object"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)
    delegating_spender = AccountId(0, 0, 400)

    proto = NftAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        serial_numbers=[1, 2, 3],
        approved_for_all=BoolValue(value=True),
        delegating_spender=delegating_spender._to_proto(),
    )
    return proto


@pytest.fixture
def proto_nft_remove_allowance():
    """Fixture for a proto NftRemoveAllowance object"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)

    proto = NftRemoveAllowanceProto(
        token_id=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        serial_numbers=[1, 2, 3],
    )
    return proto


def test_token_nft_allowance_initialization(token_nft_allowance):
    """Test the initialization of the TokenNftAllowance class"""
    assert token_nft_allowance.token_id == TokenId(0, 0, 100)
    assert token_nft_allowance.owner_account_id == AccountId(0, 0, 200)
    assert token_nft_allowance.spender_account_id == AccountId(0, 0, 300)
    assert token_nft_allowance.serial_numbers == [1, 2, 3]
    assert token_nft_allowance.approved_for_all is True
    assert token_nft_allowance.delegating_spender == AccountId(0, 0, 400)


def test_token_nft_allowance_default_initialization():
    """Test the default initialization of the TokenNftAllowance class"""
    allowance = TokenNftAllowance()
    assert allowance.token_id is None
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id is None
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is None
    assert allowance.delegating_spender is None


def test_from_proto(proto_nft_allowance):
    """Test the from_proto method of the TokenNftAllowance class"""
    allowance = TokenNftAllowance._from_proto(proto_nft_allowance)

    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.serial_numbers == [1, 2, 3]
    assert allowance.approved_for_all is True
    assert allowance.delegating_spender == AccountId(0, 0, 400)


def test_from_proto_with_empty_serial_numbers():
    """Test the from_proto method with empty serial numbers"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)

    proto = NftAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        serial_numbers=[],
        approved_for_all=BoolValue(value=False),
    )

    allowance = TokenNftAllowance._from_proto(proto)
    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is False
    assert allowance.delegating_spender is None


def test_from_proto_without_approved_for_all():
    """Test the from_proto method without approved_for_all field"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)
    spender_account_id = AccountId(0, 0, 300)

    proto = NftAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
        spender=spender_account_id._to_proto(),
        serial_numbers=[1, 2, 3],
    )

    allowance = TokenNftAllowance._from_proto(proto)
    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.spender_account_id == AccountId(0, 0, 300)
    assert allowance.serial_numbers == [1, 2, 3]
    assert allowance.approved_for_all is False
    assert allowance.delegating_spender is None


def test_from_proto_none_raises_error():
    """Test the from_proto method with a None proto"""
    with pytest.raises(ValueError, match="NftAllowance proto is None"):
        TokenNftAllowance._from_proto(None)


def test_from_wipe_proto(proto_nft_remove_allowance):
    """Test the from_wipe_proto method of the TokenNftAllowance class"""
    allowance = TokenNftAllowance._from_wipe_proto(proto_nft_remove_allowance)

    assert allowance.token_id == TokenId(0, 0, 100)
    assert allowance.owner_account_id == AccountId(0, 0, 200)
    assert allowance.serial_numbers == [1, 2, 3]
    assert allowance.spender_account_id is None
    assert allowance.approved_for_all is None
    assert allowance.delegating_spender is None


def test_from_wipe_proto_none_raises_error():
    """Test the from_wipe_proto method with a None proto"""
    with pytest.raises(ValueError, match="NftRemoveAllowance proto is None"):
        TokenNftAllowance._from_wipe_proto(None)


def test_to_proto(token_nft_allowance):
    """Test the to_proto method of the TokenNftAllowance class"""
    proto = token_nft_allowance._to_proto()

    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.owner == AccountId(0, 0, 200)._to_proto()
    assert proto.spender == AccountId(0, 0, 300)._to_proto()
    assert list(proto.serial_numbers) == [1, 2, 3]
    assert proto.approved_for_all.value is True
    assert proto.delegating_spender == AccountId(0, 0, 400)._to_proto()


def test_to_proto_with_none_values():
    """Test the to_proto method with none values"""
    allowance = TokenNftAllowance()
    proto = allowance._to_proto()

    # Protobuf fields are not None when unset, but HasField returns False
    assert not proto.HasField("tokenId")
    assert not proto.HasField("owner")
    assert not proto.HasField("spender")
    assert list(proto.serial_numbers) == []
    assert not proto.HasField("approved_for_all")
    assert not proto.HasField("delegating_spender")


def test_to_proto_with_false_approved_for_all():
    """Test the to_proto method with False approved_for_all"""
    allowance = TokenNftAllowance(
        token_id=TokenId(0, 0, 100),
        approved_for_all=False,
    )
    proto = allowance._to_proto()

    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.approved_for_all.value is False


def test_to_wipe_proto(token_nft_allowance):
    """Test the to_wipe_proto method of the TokenNftAllowance class"""
    proto = token_nft_allowance._to_wipe_proto()

    assert proto.token_id == TokenId(0, 0, 100)._to_proto()
    assert proto.owner == AccountId(0, 0, 200)._to_proto()
    assert list(proto.serial_numbers) == [1, 2, 3]


def test_to_wipe_proto_with_none_values():
    """Test the to_wipe_proto method with none values"""
    allowance = TokenNftAllowance()
    proto = allowance._to_wipe_proto()

    # Protobuf fields are not None when unset, but HasField returns False
    assert not proto.HasField("token_id")
    assert not proto.HasField("owner")
    assert list(proto.serial_numbers) == []


def test_proto_conversion_full_object(token_nft_allowance):
    """Test proto conversion with fully populated object"""
    converted = TokenNftAllowance._from_proto(token_nft_allowance._to_proto())

    assert converted.token_id == token_nft_allowance.token_id
    assert converted.owner_account_id == token_nft_allowance.owner_account_id
    assert converted.spender_account_id == token_nft_allowance.spender_account_id
    assert converted.serial_numbers == token_nft_allowance.serial_numbers
    assert converted.approved_for_all == token_nft_allowance.approved_for_all
    assert converted.delegating_spender == token_nft_allowance.delegating_spender


def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    allowance = TokenNftAllowance(
        token_id=TokenId(0, 0, 100),
        serial_numbers=[1, 2],
        approved_for_all=False,
    )
    converted = TokenNftAllowance._from_proto(allowance._to_proto())

    assert converted.token_id == allowance.token_id
    assert converted.serial_numbers == allowance.serial_numbers
    assert converted.approved_for_all == allowance.approved_for_all
    assert converted.owner_account_id is None
    assert converted.spender_account_id is None
    assert converted.delegating_spender is None


def test_wipe_proto_conversion():
    """Test wipe proto conversion"""
    allowance = TokenNftAllowance(
        token_id=TokenId(0, 0, 100),
        owner_account_id=AccountId(0, 0, 200),
        serial_numbers=[1, 2, 3],
    )
    converted = TokenNftAllowance._from_wipe_proto(allowance._to_wipe_proto())

    assert converted.token_id == allowance.token_id
    assert converted.owner_account_id == allowance.owner_account_id
    assert converted.serial_numbers == allowance.serial_numbers
    assert converted.spender_account_id is None
    assert converted.approved_for_all is None
    assert converted.delegating_spender is None


def test_string_representation(token_nft_allowance):
    """Test the string representation of TokenNftAllowance"""
    str_repr = str(token_nft_allowance)

    assert "TokenNftAllowance(" in str_repr
    assert "owner_account_id=0.0.200" in str_repr
    assert "spender_account_id=0.0.300" in str_repr
    assert "token_id=0.0.100" in str_repr
    assert "serial_numbers=[1, 2, 3]" in str_repr
    assert "approved_for_all=True" in str_repr
    assert "delegating_spender=0.0.400" in str_repr


def test_string_representation_with_none_values():
    """Test the string representation with None values"""
    allowance = TokenNftAllowance()
    str_repr = str(allowance)

    assert "TokenNftAllowance(" in str_repr
    assert "owner_account_id=None" in str_repr
    assert "spender_account_id=None" in str_repr
    assert "token_id=None" in str_repr
    assert "serial_numbers=[]" in str_repr
    assert "approved_for_all=None" in str_repr


def test_string_representation_with_empty_serial_numbers():
    """Test the string representation with empty serial numbers"""
    allowance = TokenNftAllowance(
        token_id=TokenId(0, 0, 100),
        serial_numbers=[],
    )
    str_repr = str(allowance)

    assert "serial_numbers=[]" in str_repr


def test_repr_method(token_nft_allowance):
    """Test the repr method returns the same as str"""
    assert repr(token_nft_allowance) == str(token_nft_allowance)


def test_from_proto_field_helper():
    """Test the _from_proto_field helper method"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)

    proto = NftAllowanceProto(
        tokenId=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
    )

    # Test with populated field
    result = TokenNftAllowance._from_proto_field(proto, "tokenId", TokenId._from_proto)
    assert result == token_id

    # Test with populated field
    result = TokenNftAllowance._from_proto_field(proto, "owner", AccountId._from_proto)
    assert result == owner_account_id

    # Test with empty field
    result = TokenNftAllowance._from_proto_field(proto, "spender", AccountId._from_proto)
    assert result is None


def test_from_proto_field_with_wipe_proto():
    """Test the _from_proto_field helper method with wipe proto"""
    token_id = TokenId(0, 0, 100)
    owner_account_id = AccountId(0, 0, 200)

    proto = NftRemoveAllowanceProto(
        token_id=token_id._to_proto(),
        owner=owner_account_id._to_proto(),
    )

    # Test with populated field
    result = TokenNftAllowance._from_proto_field(proto, "token_id", TokenId._from_proto)
    assert result == token_id

    # Test with populated field
    result = TokenNftAllowance._from_proto_field(proto, "owner", AccountId._from_proto)
    assert result == owner_account_id


def test_serial_numbers_edge_cases():
    """Test serial numbers with various edge cases"""
    # Test with single serial number
    allowance = TokenNftAllowance(serial_numbers=[1])
    assert allowance.serial_numbers == [1]

    # Test with large serial numbers
    allowance = TokenNftAllowance(serial_numbers=[999999, 1000000])
    assert allowance.serial_numbers == [999999, 1000000]

    # Test with zero serial number
    allowance = TokenNftAllowance(serial_numbers=[0])
    assert allowance.serial_numbers == [0]


def test_approved_for_all_edge_cases():
    """Test approved_for_all with various values"""
    # Test with True
    allowance = TokenNftAllowance(approved_for_all=True)
    assert allowance.approved_for_all is True

    # Test with False
    allowance = TokenNftAllowance(approved_for_all=False)
    assert allowance.approved_for_all is False

    # Test with None
    allowance = TokenNftAllowance(approved_for_all=None)
    assert allowance.approved_for_all is None


def test_proto_conversion_with_different_account_ids():
    """Test proto conversion with different account IDs"""
    allowance = TokenNftAllowance(
        token_id=TokenId(1, 2, 3),
        owner_account_id=AccountId(4, 5, 6),
        spender_account_id=AccountId(7, 8, 9),
        delegating_spender=AccountId(10, 11, 12),
    )
    converted = TokenNftAllowance._from_proto(allowance._to_proto())

    assert converted.token_id == TokenId(1, 2, 3)
    assert converted.owner_account_id == AccountId(4, 5, 6)
    assert converted.spender_account_id == AccountId(7, 8, 9)
    assert converted.delegating_spender == AccountId(10, 11, 12)
