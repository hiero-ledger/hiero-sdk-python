import os
import time
from typing import Optional

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.private_key import PrivateKey

# --- UTILITY FUNCTIONS (ASSUMED TO BE COPIED FROM OTHER EXAMPLES) ---

def setup_client() -> Client:
    """Initializes and returns a Client connected to the network."""
    network = Network(os.getenv('NETWORK'))
    client = Client(network)
    return client

def create_new_account(client: Client) -> tuple[AccountId, PrivateKey]:
    """Creates a new Hedera account for use as a fee collector."""
    private_key = PrivateKey.generate()
    
    response = (
        AccountCreateTransaction()
        .set_key(private_key)
        .set_initial_balance(100) # 100 tinybar for creation
        .execute(client)
    )
    receipt = response.get_receipt(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        raise Exception(f"Account creation failed with status: {receipt.status.name}")

    account_id = receipt.account_id
    print(f"Fee Collector Account created: {account_id}")
    return account_id, private_key

# --- END UTILITY FUNCTIONS ---


def create_token_with_fractional_fee(client: Client, fee_collector_id: AccountId):
    """
    Creates a new token and attaches the custom fractional fee, returning the token ID.
    """
    
    # 1. DEFINE THE CUSTOM FRACTIONAL FEE
    fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=100,  # 1% fee
        min_amount=1,
        max_amount=50,
        assessment_method=FeeAssessmentMethod.INCLUSIVE, # Example assessment method
        fee_collector_account_id=fee_collector_id,
        all_collectors_are_exempt=False,
    )
    
    # 2. CREATE THE TOKEN TRANSACTION
    token_name = f"FractionalTest{int(time.time())}"
    
    response = (
        TokenCreateTransaction()
        .set_token_name(token_name)
        .set_token_symbol("FRAC")
        .set_treasury_account_id(client.operator_account_id)
        .set_initial_supply(1000)
        .set_custom_fees([fractional_fee]) # ADD THE CUSTOM FEE HERE
        .execute(client)
    )
    
    receipt = response.get_receipt(client)
    if receipt.status != ResponseCode.SUCCESS:
        raise Exception(f"Token creation failed with status: {receipt.status.name}")

    token_id = receipt.token_id
    print(f"Token created with Fractional Fee: {token_id}")
    return token_id


def verify_token_fee(client: Client, token_id: AccountId, fee_collector_id: AccountId):
    """
    Queries the token info and verifies the custom fractional fee is correctly applied.
    """
    print("\n--- Verifying Custom Fee ---")
    
    token_info = (
        TokenInfoQuery()
        .set_token_id(token_id)
        .execute(client)
    )

    if not token_info.custom_fees:
        raise Exception("Verification Failed: Custom fee list is empty.")
    
    # The first fee should be the fractional fee we added
    fee = token_info.custom_fees[0] 
    
    if not isinstance(fee, CustomFractionalFee):
        raise Exception("Verification Failed: Fee is not CustomFractionalFee type.")
    
    if fee.numerator != 1 or fee.denominator != 100:
        raise Exception("Verification Failed: Fractional ratio is incorrect.")

    if fee.fee_collector_account_id != fee_collector_id:
        raise Exception("Verification Failed: Collector ID is incorrect.")

    print("Verification Successful: Fractional fee correctly attached and verified.")
    

def main():
    """
    Main function to run the end-to-end fractional fee example.
    """
    client = setup_client()
    
    try:
        # 1. Create Fee Collector Account
        fee_collector_id, _ = create_new_account(client)
        
        # 2. Create Token with the Fractional Fee attached
        token_id = create_token_with_fractional_fee(client, fee_collector_id)
        
        # 3. Verify the fee is correctly applied to the token
        verify_token_fee(client, token_id, fee_collector_id)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    # Ensure you set the NETWORK and OPERATOR_KEY environment variables
    if not os.getenv('NETWORK') or not os.getenv('OPERATOR_KEY'):
        print("FATAL: Please set NETWORK and OPERATOR_KEY environment variables.")
    else:
        main()