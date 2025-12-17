"""
Unit tests for the CustomFeeLimit class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.custom_fees_pb2 import (
    CustomFeeLimit as CustomFeeLimitProto,
)
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit

pytestmark = pytest.mark.unit


@pytest.fixture
def custom_fixed_fee():
    """Fixture for a CustomFixedFee object"""
    return CustomFixedFee(
        amount=1000,
        denominating_token_id=TokenId(0, 0, 500),
        fee_collector_account_id=AccountId(0, 0, 600),
    )


@pytest.fixture
def multiple_custom_fees():
    """Fixture for multiple CustomFixedFee objects"""
    return [
        CustomFixedFee(
            amount=1000,
            denominating_token_id=TokenId(0, 0, 500),
            fee_collector_account_id=AccountId(0, 0, 600),
        ),
        CustomFixedFee(
            amount=2000,
            denominating_token_id=TokenId(0, 0, 700),
            fee_collector_account_id=AccountId(0, 0, 800),
        ),
    ]


@pytest.fixture
def custom_fee_limit(custom_fixed_fee):
    """Fixture for a CustomFeeLimit object"""
    return CustomFeeLimit(
        payer_id=AccountId(0, 0, 100),
        custom_fees=[custom_fixed_fee],
    )


@pytest.fixture
def proto_custom_fee_limit(custom_fixed_fee):
    """Fixture for a proto CustomFeeLimit object"""
    from hiero_sdk_python.hapi.services.custom_fees_pb2 import FixedFee

    proto = CustomFeeLimitProto(
        account_id=AccountId(0, 0, 100)._to_proto(),
        fees=[
            FixedFee(
                amount=custom_fixed_fee.amount,
                denominating_token_id=(
                    custom_fixed_fee.denominating_token_id._to_proto()
                    if custom_fixed_fee.denominating_token_id
                    else None
                ),
            )
        ],
    )
    return proto


def test_custom_fee_limit_initialization(custom_fee_limit):
    """Test the initialization of the CustomFeeLimit class"""
    assert custom_fee_limit.payer_id == AccountId(0, 0, 100)
    assert len(custom_fee_limit.custom_fees) == 1
    assert custom_fee_limit.custom_fees[0].amount == 1000
    assert custom_fee_limit.custom_fees[0].denominating_token_id == TokenId(0, 0, 500)
    assert custom_fee_limit.custom_fees[0].fee_collector_account_id == AccountId(
        0, 0, 600
    )


def test_custom_fee_limit_default_initialization():
    """Test the default initialization of the CustomFeeLimit class"""
    custom_fee_limit = CustomFeeLimit()
    assert custom_fee_limit.payer_id is None
    assert not custom_fee_limit.custom_fees


def test_set_payer_id():
    """Test setting the payer ID"""
    custom_fee_limit = CustomFeeLimit()
    payer_id = AccountId(0, 0, 200)

    result = custom_fee_limit.set_payer_id(payer_id)

    assert custom_fee_limit.payer_id == payer_id
    assert result is custom_fee_limit  # Method chaining


def test_set_payer_id_to_none():
    """Test setting the payer ID to None"""
    custom_fee_limit = CustomFeeLimit()
    custom_fee_limit.payer_id = AccountId(0, 0, 200)  # Set initial value

    result = custom_fee_limit.set_payer_id(None)

    assert custom_fee_limit.payer_id is None
    assert result is custom_fee_limit  # Method chaining


def test_add_custom_fee():
    """Test adding a custom fee"""
    custom_fee_limit = CustomFeeLimit()
    custom_fee = CustomFixedFee(
        amount=1500,
        denominating_token_id=TokenId(0, 0, 900),
        fee_collector_account_id=AccountId(0, 0, 1000),
    )

    result = custom_fee_limit.add_custom_fee(custom_fee)

    assert len(custom_fee_limit.custom_fees) == 1
    assert custom_fee_limit.custom_fees[0] == custom_fee
    assert result is custom_fee_limit  # Method chaining


def test_set_custom_fees():
    """Test setting the custom fees list"""
    custom_fee_limit = CustomFeeLimit()
    custom_fees = [
        CustomFixedFee(
            amount=1000,
            denominating_token_id=TokenId(0, 0, 500),
            fee_collector_account_id=AccountId(0, 0, 600),
        ),
        CustomFixedFee(
            amount=2000,
            denominating_token_id=TokenId(0, 0, 700),
            fee_collector_account_id=AccountId(0, 0, 800),
        ),
    ]

    result = custom_fee_limit.set_custom_fees(custom_fees)

    assert len(custom_fee_limit.custom_fees) == 2
    assert custom_fee_limit.custom_fees == custom_fees
    assert result is custom_fee_limit  # Method chaining


def test_set_custom_fees_to_empty_list():
    """Test setting custom fees to an empty list"""
    custom_fee_limit = CustomFeeLimit()
    custom_fee_limit.custom_fees = [CustomFixedFee(amount=1000)]  # Set initial value

    result = custom_fee_limit.set_custom_fees([])

    assert not custom_fee_limit.custom_fees
    assert result is custom_fee_limit  # Method chaining


def test_from_proto(proto_custom_fee_limit):
    """Test the from_proto method of the CustomFeeLimit class"""
    custom_fee_limit = CustomFeeLimit._from_proto(proto_custom_fee_limit)

    assert custom_fee_limit.payer_id == AccountId(0, 0, 100)
    assert len(custom_fee_limit.custom_fees) == 1
    assert custom_fee_limit.custom_fees[0].amount == 1000
    assert custom_fee_limit.custom_fees[0].denominating_token_id == TokenId(0, 0, 500)
    # fee_collector_account_id is not part of FixedFee, so it should be None
    assert custom_fee_limit.custom_fees[0].fee_collector_account_id is None


def test_from_proto_with_empty_fees():
    """Test the from_proto method of the CustomFeeLimit class with empty fees"""
    proto = CustomFeeLimitProto(
        account_id=AccountId(0, 0, 100)._to_proto(),
        fees=[],
    )

    custom_fee_limit = CustomFeeLimit._from_proto(proto)
    assert custom_fee_limit.payer_id == AccountId(0, 0, 100)
    assert not custom_fee_limit.custom_fees


def test_from_proto_without_payer_id():
    """Test the from_proto method of the CustomFeeLimit class without payer ID"""
    from hiero_sdk_python.hapi.services.custom_fees_pb2 import FixedFee

    custom_fee = CustomFixedFee(
        amount=1000,
        denominating_token_id=TokenId(0, 0, 500),
        fee_collector_account_id=AccountId(0, 0, 600),
    )
    proto = CustomFeeLimitProto(
        fees=[
            FixedFee(
                amount=custom_fee.amount,
                denominating_token_id=(
                    custom_fee.denominating_token_id._to_proto()
                    if custom_fee.denominating_token_id
                    else None
                ),
            )
        ],
    )

    custom_fee_limit = CustomFeeLimit._from_proto(proto)
    assert custom_fee_limit.payer_id is None
    assert len(custom_fee_limit.custom_fees) == 1


def test_from_proto_none_raises_error():
    """Test the from_proto method of the CustomFeeLimit class with a None proto"""
    with pytest.raises(ValueError, match="Custom fee limit proto is None"):
        CustomFeeLimit._from_proto(None)


def test_to_proto(custom_fee_limit):
    """Test the to_proto method of the CustomFeeLimit class"""
    proto = custom_fee_limit._to_proto()

    assert proto.account_id == AccountId(0, 0, 100)._to_proto()
    assert len(proto.fees) == 1
    assert proto.fees[0].amount == 1000
    assert proto.fees[0].denominating_token_id == TokenId(0, 0, 500)._to_proto()


def test_to_proto_with_none_values():
    """Test the to_proto method of the CustomFeeLimit class with none values"""
    custom_fee_limit = CustomFeeLimit()
    proto = custom_fee_limit._to_proto()

    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, "account_id")
    assert not proto.fees  # Empty list for fees


def test_to_proto_with_empty_fees():
    """Test the to_proto method of the CustomFeeLimit class with empty fees list"""
    custom_fee_limit = CustomFeeLimit(
        payer_id=AccountId(0, 0, 100),
        custom_fees=[],
    )
    proto = custom_fee_limit._to_proto()

    assert proto.account_id == AccountId(0, 0, 100)._to_proto()
    assert not proto.fees


def test_to_proto_without_payer_id():
    """Test the to_proto method of the CustomFeeLimit class without payer ID"""
    custom_fee = CustomFixedFee(
        amount=1000,
        denominating_token_id=TokenId(0, 0, 500),
        fee_collector_account_id=AccountId(0, 0, 600),
    )
    custom_fee_limit = CustomFeeLimit(custom_fees=[custom_fee])
    proto = custom_fee_limit._to_proto()

    assert not proto.HasField("account_id")
    assert len(proto.fees) == 1


def test_proto_conversion_full_object(custom_fee_limit):
    """Test proto conversion with fully populated object"""
    converted = CustomFeeLimit._from_proto(custom_fee_limit._to_proto())

    assert converted.payer_id == custom_fee_limit.payer_id
    assert len(converted.custom_fees) == len(custom_fee_limit.custom_fees)
    assert converted.custom_fees[0].amount == custom_fee_limit.custom_fees[0].amount
    assert (
        converted.custom_fees[0].denominating_token_id
        == custom_fee_limit.custom_fees[0].denominating_token_id
    )
    # fee_collector_account_id is not preserved
    assert converted.custom_fees[0].fee_collector_account_id is None


def test_proto_conversion_multiple_fees(multiple_custom_fees):
    """Test proto conversion with multiple custom fees"""
    custom_fee_limit = CustomFeeLimit(
        payer_id=AccountId(0, 0, 100),
        custom_fees=multiple_custom_fees,
    )
    converted = CustomFeeLimit._from_proto(custom_fee_limit._to_proto())

    assert len(converted.custom_fees) == 2

    first = converted.custom_fees[0]
    second = converted.custom_fees[1]

    assert first.amount == 1000
    assert first.denominating_token_id == TokenId(0, 0, 500)
    assert second.amount == 2000
    assert second.denominating_token_id == TokenId(0, 0, 700)


def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    custom_fee_limit = CustomFeeLimit(
        payer_id=AccountId(0, 0, 200),
    )
    converted = CustomFeeLimit._from_proto(custom_fee_limit._to_proto())

    assert converted.payer_id == custom_fee_limit.payer_id
    assert not converted.custom_fees


def test_method_chaining():
    """Test method chaining functionality"""
    custom_fee_limit = CustomFeeLimit()
    payer_id = AccountId(0, 0, 300)
    custom_fee = CustomFixedFee(
        amount=3000,
        denominating_token_id=TokenId(0, 0, 900),
        fee_collector_account_id=AccountId(0, 0, 1000),
    )

    result = (
        custom_fee_limit.set_payer_id(payer_id)
        .add_custom_fee(custom_fee)
        .set_custom_fees([custom_fee])
    )

    assert result is custom_fee_limit
    assert custom_fee_limit.payer_id == payer_id
    assert len(custom_fee_limit.custom_fees) == 1
    assert custom_fee_limit.custom_fees[0] == custom_fee


def test_string_representation(custom_fee_limit):
    """Test the string representation of CustomFeeLimit"""
    string_repr = str(custom_fee_limit)

    assert "CustomFeeLimit(" in string_repr
    assert "payer_id=0.0.100" in string_repr
    assert "custom_fees=" in string_repr
    assert "CustomFixedFee" in string_repr


def test_string_representation_empty():
    """Test the string representation of empty CustomFeeLimit"""
    custom_fee_limit = CustomFeeLimit()
    string_repr = str(custom_fee_limit)

    assert "CustomFeeLimit(" in string_repr
    assert "payer_id=None" in string_repr
    assert "custom_fees=[]" in string_repr


def test_repr_equals_str(custom_fee_limit):
    """Test that __repr__ equals __str__"""
    assert repr(custom_fee_limit) == str(custom_fee_limit)
