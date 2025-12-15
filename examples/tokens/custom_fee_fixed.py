"""
Run with: 
uv run examples/tokens/custom_fixed_fee.py
python examples/tokens/custom_fixed_fee.py
"""
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId

def custom_fixed_fee():
    fixed_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    print("\n--- Custom Fixed Fee ---")
    print(fixed_fee)

    # Convert to protobuf
    fixed_fee_proto = fixed_fee._to_proto()
    
    print("Fixed Fee Protobuf:", fixed_fee_proto)
    
    
if __name__ == "__main__":
    custom_fixed_fee()