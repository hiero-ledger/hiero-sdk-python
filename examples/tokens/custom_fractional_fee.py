"""
Run with: 
uv run examples/tokens/custom_fractional_fee.py
python examples/tokens/custom_fractional_fee.py
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
    print(fractional_fee.__str__())


    # Convert to protobuf
    fractional_fee_proto = fractional_fee._to_proto()

    print("Fractional Fee Protobuf:", fractional_fee_proto)

if __name__ == "__main__":
    custom_fractional_fee()
