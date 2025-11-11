"""
Run with: 
uv run examples/custom_royalty_fee.py
python examples/custom_royalty_fee.py
"""
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId

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
    print(f"Fallback Fee Amount: {royalty_fee.fallback_fee.amount if royalty_fee.fallback_fee is not None else 'None'}")
    print(f"Fallback Fee Denominating Token ID: {royalty_fee.fallback_fee.denominating_token_id if royalty_fee.fallback_fee is not None else 'None'}")
    print(f"Fee Collector Account ID: {royalty_fee.fee_collector_account_id}")
    print(f"All Collectors Exempt: {royalty_fee.all_collectors_are_exempt}")

    # Convert to protobuf
    royalty_fee_proto = royalty_fee._to_proto()

    print("Royalty Fee Protobuf:", royalty_fee_proto)

if __name__ == "__main__":
    custom_royalty_fee()