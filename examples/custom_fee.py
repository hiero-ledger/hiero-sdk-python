"""
Example demonstrating custom fee functionality.

Run:
uv run examples/custom_fee.py
python examples/custom_fee.py
"""

from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId


def setup_client():
    """Initialize environment if needed."""
    pass  # No client setup required for this example


def custom_fixed_fee():
    """Create and display a CustomFixedFee."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    print("\nCustomFixedFee")
    print(f"Amount: {fee.amount}")
    print(f"Denominating Token ID: {fee.denominating_token_id}")
    print(f"Fee Collector Account ID: {fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {fee.all_collectors_are_exempt}")
    print("Protobuf:", fee._to_proto())


def custom_fractional_fee():
    """Create and display a CustomFractionalFee."""
    fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    print("\nCustomFractionalFee")
    print(f"Numerator: {fee.numerator}")
    print(f"Denominator: {fee.denominator}")
    print(f"Min Amount: {fee.min_amount}")
    print(f"Max Amount: {fee.max_amount}")
    print(f"Assessment Method: {fee.assessment_method}")
    print(f"Fee Collector Account ID: {fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {fee.all_collectors_are_exempt}")
    print("Protobuf:", fee._to_proto())


def custom_royalty_fee():
    """Create and display a CustomRoyaltyFee."""
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

    print("\nCustomRoyaltyFee")
    print(f"Numerator: {fee.numerator}")
    print(f"Denominator: {fee.denominator}")
    print(f"Fallback Fee Amount: {fee.fallback_fee.amount}")
    print(f"Fallback Fee Token ID: {fee.fallback_fee.denominating_token_id}")
    print(f"Fee Collector Account ID: {fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {fee.all_collectors_are_exempt}")
    print("Protobuf:", fee._to_proto())


def main():
    setup_client()
    custom_fixed_fee()
    custom_fractional_fee()
    custom_royalty_fee()


if __name__ == "__main__":
    main()
