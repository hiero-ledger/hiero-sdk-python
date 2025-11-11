"""
Run with: 
uv run examples/custom_fractional_fee.py
python examples/custom_fractional_fee.py
"""
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.account.account_id import AccountId

def custom_fractional_fee() :
    fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    print("\nCustomFractionalFee:")
    print(f"Numerator: {fractional_fee.numerator}")
    print(f"Denominator: {fractional_fee.denominator}")
    print(f"Min Amount: {fractional_fee.min_amount}")
    print(f"Max Amount: {fractional_fee.max_amount}")
    print(f"Assessment Method: {fractional_fee.assessment_method}")
    print(f"Fee Collector Account ID: {fractional_fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {fractional_fee.all_collectors_are_exempt}")

    # Convert to protobuf
    fractional_fee_proto = fractional_fee._to_proto()

    print("Fractional Fee Protobuf:", fractional_fee_proto)

if __name__ == "__main__":
    custom_fractional_fee()