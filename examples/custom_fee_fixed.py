"""
Example for creating and displaying a CustomFixedFee object.

This example demonstrates:
1.  How to instantiate CustomFixedFee.
2.  The output of the new __repr__ method for clear debugging.
3.  How to convert the fee object to its protobuf representation.

Run with:
uv run examples/custom_fixed_fee.py
python examples/custom_fixed_fee.py
"""
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId

def demonstrate_custom_fixed_fee():
    """Creates and displays a CustomFixedFee."""
    
    # 1. Create the CustomFixedFee object
    fixed_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    # 2. Print the object directly to see the __repr__ output
    print("--- CustomFixedFee (using __repr__) ---")
    print(fixed_fee)
    
    # 3. Convert to protobuf
    fixed_fee_proto = fixed_fee._to_proto()
    
    print("\n--- Fixed Fee Protobuf ---")
    print(fixed_fee_proto)
    
    
if __name__ == "__main__":
    # Call the main function when the script is executed
    demonstrate_custom_fixed_fee()