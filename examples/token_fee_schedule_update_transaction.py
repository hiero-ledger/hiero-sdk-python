import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_fungible_token_with_custom_fees(client, operator_id, operator_key):
    """Create a fungible token with initial custom fees and fee schedule key"""
    # Create initial custom fees
    initial_fixed_fee = CustomFixedFee(
        amount=5,
        fee_collector_account_id=operator_id,
        all_collectors_are_exempt=False,
    )
    
    initial_fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=20,  # 5% fee
        min_amount=1,
        max_amount=50,
        assessment_method=FeeAssessmentMethod.INCLUSIVE,
        fee_collector_account_id=operator_id,
        all_collectors_are_exempt=False,
    )
    
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(10000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_custom_fees([initial_fixed_fee, initial_fractional_fee])
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def get_token_info(client, token_id):
    """Get and display token information including custom fees"""
    token_info = (
        TokenInfoQuery()
        .set_token_id(token_id)
        .execute(client)
    )
    
    print(f"Token Name: {token_info.name}")
    print(f"Token Symbol: {token_info.symbol}")
    print(f"Custom Fees Count: {len(token_info.custom_fees)}")
    
    for i, fee in enumerate(token_info.custom_fees):
        print(f"  Fee {i + 1}:")
        if hasattr(fee, 'amount'):  # Fixed fee
            print(f"    Type: Fixed Fee")
            print(f"    Amount: {fee.amount}")
            if hasattr(fee, 'denominating_token_id') and fee.denominating_token_id:
                print(f"    Denominating Token: {fee.denominating_token_id}")
            else:
                print(f"    Denominating Token: HBAR")
        elif hasattr(fee, 'numerator'):  # Fractional fee
            print(f"    Type: Fractional Fee")
            print(f"    Fraction: {fee.numerator}/{fee.denominator}")
            if hasattr(fee, 'min_amount'):
                print(f"    Min Amount: {fee.min_amount}")
            if hasattr(fee, 'max_amount'):
                print(f"    Max Amount: {fee.max_amount}")
            if hasattr(fee, 'assessment_method'):
                print(f"    Assessment Method: {fee.assessment_method}")
        
        if hasattr(fee, 'fee_collector_account_id'):
            print(f"    Fee Collector: {fee.fee_collector_account_id}")
        if hasattr(fee, 'all_collectors_are_exempt'):
            print(f"    All Collectors Exempt: {fee.all_collectors_are_exempt}")
    
    return token_info

def update_fee_schedule(client, token_id, operator_key):
    """Update the token's fee schedule with new custom fees"""
    # Create new custom fees for the update
    new_fixed_fee = CustomFixedFee(
        amount=10,  # Increased from 5
        fee_collector_account_id=AccountId.from_string(os.getenv('OPERATOR_ID')),
        all_collectors_are_exempt=False,
    )
    
    new_fractional_fee = CustomFractionalFee(
        numerator=3,
        denominator=100,  # 3% fee (changed from 5%)
        min_amount=2,     # Increased minimum
        max_amount=100,   # Increased maximum
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,  # Changed assessment method
        fee_collector_account_id=AccountId.from_string(os.getenv('OPERATOR_ID')),
        all_collectors_are_exempt=True,  # Changed to exempt collectors
    )
    
    # Add a third fee
    additional_fixed_fee = CustomFixedFee(
        amount=1,
        fee_collector_account_id=AccountId.from_string(os.getenv('OPERATOR_ID')),
        all_collectors_are_exempt=True,
    )
    
    receipt = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees([new_fixed_fee, new_fractional_fee, additional_fixed_fee])
        .freeze_with(client)
        .sign(operator_key)  # Sign with operator key (admin key can update fee schedule)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token fee schedule update failed with status: {ResponseCode(receipt.status).name}")
        if receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY:
            print("Note: This token was not created with a fee schedule key, so fee schedule updates are not allowed.")
        sys.exit(1)
    
    print("Successfully updated token fee schedule")

def clear_fee_schedule(client, token_id, operator_key):
    """Clear all custom fees from the token"""
    receipt = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees([])  # Empty list removes all custom fees
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token fee schedule clear failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print("Successfully cleared all custom fees from token")

def token_fee_schedule_update():
    """
    Demonstrates the token fee schedule update functionality by:
    1. Setting up client with operator account
    2. Creating a fungible token with initial custom fees
    3. Displaying initial token info and custom fees
    4. Attempting to update the fee schedule (may fail if no fee schedule key)
    5. Clearing all custom fees from the token
    6. Displaying final token info
    """
    client, operator_id, operator_key = setup_client()
    
    # Create a fungible token with initial custom fees
    token_id = create_fungible_token_with_custom_fees(client, operator_id, operator_key)
    
    # Display initial token info
    print("\nToken info with initial custom fees:")
    get_token_info(client, token_id)
    
    # Attempt to update the fee schedule
    print("\nAttempting to update fee schedule...")
    try:
        update_fee_schedule(client, token_id, operator_key)
        
        # Display updated token info only if update succeeded
        print("\nToken info after fee schedule update:")
        get_token_info(client, token_id)
        
        # Clear all custom fees
        print("\nClearing all custom fees...")
        clear_fee_schedule(client, token_id, operator_key)
        
        # Display final token info
        print("\nToken info after clearing custom fees:")
        get_token_info(client, token_id)
        
    except SystemExit:
        print("\nFee schedule update failed. This is expected if the token was created without a fee schedule key.")
        print("Custom fees were set during token creation, but cannot be modified after creation without a fee schedule key.")

if __name__ == "__main__":
    token_fee_schedule_update()
