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



def custom_fixed_fee():
    fixed_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    print("CustomFixedFee:")
    print(f"Amount: {fixed_fee.amount}")
    print(f"Denominating Token ID: {fixed_fee.denominating_token_id}")
    print(f"Fee Collector Account ID: {fixed_fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {fixed_fee.all_collectors_are_exempt}")
    # Convert to protobuf
    fixed_fee_proto = fixed_fee._to_proto()
    
    print("Fixed Fee Protobuf:", fixed_fee_proto)

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

def custom_royalty_fee():
    fallback_fee = CustomFixedFee(
        amount=50,
        denominating_token_id=TokenId(0, 0, 789),
    )
    royalty_fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )
    print("\nCustomRoyaltyFee:")
    print(f"Numerator: {royalty_fee.numerator}")
    print(f"Denominator: {royalty_fee.denominator}")
    print(f"Fallback Fee Amount: {royalty_fee.fallback_fee.amount}")
    print(f"Fallback Fee Denominating Token ID: {royalty_fee.fallback_fee.denominating_token_id}")
    print(f"Fee Collector Account ID: {royalty_fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {royalty_fee.all_collectors_are_exempt}")

    # Convert to protobuf
    royalty_fee_proto = royalty_fee._to_proto()

    print("Royalty Fee Protobuf:", royalty_fee_proto)

def custom_fee():
    #create a CustomFixedFee
    custom_fixed_fee()
    #create a CustomFractionalFee
    custom_fractional_fee()
    #create a CustomRoyaltyFee
    custom_royalty_fee()

def main():
    #setup a Client
    custom_fee()

if __name__ == "__main__":
    main()