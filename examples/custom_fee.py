"""
Run with: 
uv run examples/custom_fee.py
python examples/custom_fee.py
"""
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId


def pretty_key(attr: str) -> str:
    """Convert snake_case to Capitalized Words (ID stays uppercase)."""
    parts = attr.split("_")
    return " ".join([p.upper() if p in ("id", "ids") else p.capitalize() for p in parts])


def print_fee_details(fee, fee_type: str):
    """Print attributes of a fee object in clean key-value style (flatten nested fees)."""
    print(f"\n{fee_type}:")
    for attr, value in vars(fee).items():
        if value is None:
            continue
        key = pretty_key(attr)
        if isinstance(value, (CustomFixedFee, CustomFractionalFee, CustomRoyaltyFee)):
            # Flatten nested fee attributes with prefix
            for sub_attr, sub_value in vars(value).items():
                if sub_value is None:
                    continue
                sub_key = f"{key} {pretty_key(sub_attr)}"
                print(f"{sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
    print(f"Protobuf: {fee._to_proto()}")


def demo_fixed_fee():
    # Create a CustomFixedFee
    fixed_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    print_fee_details(fixed_fee, "CustomFixedFee")


def demo_fractional_fee():
    # Create a CustomFractionalFee
    fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    print_fee_details(fractional_fee, "CustomFractionalFee")


def demo_royalty_fee():
    # Create a CustomRoyaltyFee
    fallback_fee = CustomFixedFee(
        amount=50,
        denominating_token_id=TokenId(0, 0, 789),
        all_collectors_are_exempt=False,
    )
    royalty_fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )
    print_fee_details(royalty_fee, "CustomRoyaltyFee")


def main():
    demo_fixed_fee()
    demo_fractional_fee()
    demo_royalty_fee()


if __name__ == "__main__":
    main()
