import pytest
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit

# --- ADDED TESTS FOR ISSUE #583: __repr__ VERIFICATION ---

def test_custom_fixed_fee_repr():
    """Verifies the __repr__ output for CustomFixedFee."""
    # Use the same setup values as test_custom_fixed_fee
    fee_collector_id = AccountId(0, 0, 456)
    
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=fee_collector_id,
        all_collectors_are_exempt=True,
    )
    
    # The expected string must match the format implemented in CustomFee.__repr__
    # Note the use of repr() on the objects to match the f-string's !r formatting
    expected_repr = (
        f"CustomFixedFee("
        f"fee_collector_account_id={repr(fee_collector_id)}, "
        f"all_collectors_are_exempt=True)"
    )
    assert repr(fee) == expected_repr

def test_custom_fractional_fee_repr():
    """Verifies the __repr__ output for CustomFractionalFee."""
    # Use the same setup values as test_custom_fractional_fee
    fee_collector_id = AccountId(0, 0, 456)
    
    fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=fee_collector_id,
        all_collectors_are_exempt=False,
    )
    
    expected_repr = (
        f"CustomFractionalFee("
        f"fee_collector_account_id={repr(fee_collector_id)}, "
        f"all_collectors_are_exempt=False)"
    )
    assert repr(fee) == expected_repr

def test_custom_royalty_fee_repr():
    """Verifies the __repr__ output for CustomRoyaltyFee."""
    # Use the same setup values as test_custom_royalty_fee
    fee_collector_id = AccountId(0, 0, 456)
    
    fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=None, # Note: fallback_fee is NOT part of the base __repr__
        fee_collector_account_id=fee_collector_id,
        all_collectors_are_exempt=True,
    )
    
    expected_repr = (
        f"CustomRoyaltyFee("
        f"fee_collector_account_id={repr(fee_collector_id)}, "
        f"all_collectors_are_exempt=True)"
    )
    assert repr(fee) == expected_repr

def test_custom_fixed_fee():
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )

    proto = fee._to_proto()  # Changed from _to_protobuf
    new_fee = CustomFixedFee._from_proto(proto)  # Changed from CustomFee._from_protobuf

    assert isinstance(new_fee, CustomFixedFee)
    assert new_fee.amount == 100
    assert new_fee.denominating_token_id == TokenId(0, 0, 123)
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is True

def test_custom_fractional_fee():
    fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    proto = fee._to_proto()  # Changed from _to_protobuf
    new_fee = CustomFractionalFee._from_proto(proto)  # Changed from CustomFee._from_protobuf

    assert isinstance(new_fee, CustomFractionalFee)
    assert new_fee.numerator == 1
    assert new_fee.denominator == 10
    assert new_fee.min_amount == 1
    assert new_fee.max_amount == 100
    assert new_fee.assessment_method == FeeAssessmentMethod.EXCLUSIVE
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is False

def test_custom_royalty_fee():
    fallback_fee = CustomFixedFee(
        amount=50,
        denominating_token_id=TokenId(0, 0, 789),
    )
    fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )

    proto = fee._to_proto()  # Changed from _to_protobuf
    new_fee = CustomRoyaltyFee._from_proto(proto)  # Changed from CustomFee._from_protobuf

    assert isinstance(new_fee, CustomRoyaltyFee)
    assert new_fee.numerator == 5
    assert new_fee.denominator == 100
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is True
    assert isinstance(new_fee.fallback_fee, CustomFixedFee)
    assert new_fee.fallback_fee.amount == 50
    assert new_fee.fallback_fee.denominating_token_id == TokenId(0, 0, 789)
    
    
    
