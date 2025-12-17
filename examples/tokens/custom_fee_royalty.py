"""
Run with:
uv run examples/tokens/custom_royalty_fee.py
python examples/tokens/custom_royalty_fee.py
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
    print(royalty_fee)

    # Convert to protobuf
    royalty_fee_proto = royalty_fee._to_proto()

    print("Royalty Fee Protobuf:", royalty_fee_proto)


if __name__ == "__main__":
    custom_royalty_fee()
