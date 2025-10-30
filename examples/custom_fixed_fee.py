"""Example demonstrating the creation and representation of CustomFixedFee objects."""

import os
import sys
from dotenv import load_dotenv
from typing import Optional, Tuple

# Hiero SDK imports
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hbar import Hbar

# Load environment variables from .env file
load_dotenv()

def setup_client_and_collector() -> Optional[Tuple[Client, AccountId]]:
    """Sets up the client and identifies the fee collector account."""
    try:
        client = Client.from_env()
    except ValueError as e:
        print(f"Error: Client configuration failed. Check your .env file. Details: {e}")
        return None

    fee_collector_id_str = os.getenv("OPERATOR_ID")
    if not fee_collector_id_str:
        print("Warning: OPERATOR_ID not found. Using default 0.0.0 for fee collector.")
        fee_collector_id = AccountId(0, 0, 0)
    else:
        try:
            fee_collector_id = AccountId.from_string(fee_collector_id_str)
        except ValueError as e:
            print(f"Error: Invalid OPERATOR_ID format '{fee_collector_id_str}'. {e}")
            return None
    
    return client, fee_collector_id

def create_hbar_fee(fee_collector_id: AccountId):
    """Creates and prints a CustomFixedFee denominated in HBAR."""
    print("\n1. CustomFixedFee (HBAR):")
    try:
        hbar_fee = CustomFixedFee(
            amount=Hbar(1).to_tinybars(),  
            fee_collector_account_id=fee_collector_id
        )
        print(hbar_fee)
    except Exception as e:
        print(f"Error creating HBAR fee: {e}")

def create_token_fee(fee_collector_id: AccountId):
    """Creates and prints a CustomFixedFee denominated in a specific token."""
    print("\n2. CustomFixedFee (Specific Token):")
    token_id_str = os.getenv("TOKEN_ID", "0.0.12345") 
    try:
        denom_token_id = TokenId.from_string(token_id_str)
        token_fee = CustomFixedFee(
            amount=50, 
            denominating_token_id=denom_token_id,
            fee_collector_account_id=fee_collector_id,
            all_collectors_are_exempt=True 
        )
        print(token_fee)
    except ValueError as e:
        print(f"Error creating token fee (using token ID '{token_id_str}'): {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def create_same_token_fee(fee_collector_id: AccountId):
    """Creates and prints a CustomFixedFee denominated in the attached token (0.0.0)."""
    print("\n3. CustomFixedFee (Same Token - Sentinel 0.0.0):")
    try:
        same_token_fee = CustomFixedFee(
            amount=10, 
            fee_collector_account_id=fee_collector_id
        )
        same_token_fee.set_denominating_token_to_same_token()
        print(same_token_fee)
    except Exception as e:
        print(f"Error creating same-token fee: {e}")

def main():
    """Main function to set up client and run CustomFixedFee examples."""
    print("--- Creating CustomFixedFee examples ---")
    
    setup_result = setup_client_and_collector()
    if setup_result is None:
        print("Exiting due to setup failure.")
        sys.exit(1)

    _client, fee_collector_id = setup_result
    
    create_hbar_fee(fee_collector_id)
    create_token_fee(fee_collector_id)
    create_same_token_fee(fee_collector_id)

    print("\n--- Example finished ---")

if __name__ == "__main__":
    main()