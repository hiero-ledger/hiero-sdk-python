"""Example demonstrating the creation and representation of CustomFixedFee objects."""

import os
from dotenv import load_dotenv

# Hiero SDK imports
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hbar import Hbar

load_dotenv()

def main():
    """Example function to create and display CustomFixedFee instances."""
    try:
        client = Client.from_env()
    except ValueError as e:
        print(f"Error: Client configuration failed. Check your .env file. Details: {e}")
        return

    print("--- Creating CustomFixedFee examples ---")

    fee_collector_id_str = os.getenv("OPERATOR_ID")
    if not fee_collector_id_str:
        print("Warning: OPERATOR_ID not found in .env. Using default 0.0.0 for fee collector.")
        fee_collector_id = AccountId(0, 0, 0)
    else:
        try:
            fee_collector_id = AccountId.from_string(fee_collector_id_str)
        except ValueError as e:
            print(f"Error: Invalid OPERATOR_ID format '{fee_collector_id_str}'. {e}")
            return

    # Example 1: Fixed fee in HBAR (1 Hbar)
    try:
        hbar_fee = CustomFixedFee(
            amount=Hbar(1).to_tinybars(),
            fee_collector_account_id=fee_collector_id
        )
        print("\n1. CustomFixedFee (HBAR):")
        print(hbar_fee)
    except Exception as e:
        print(f"Error creating HBAR fee: {e}")


    # Example 2: Fixed fee in a specific fungible token
    token_id_str = os.getenv("TOKEN_ID", "0.0.12345") 
    try:
        denom_token_id = TokenId.from_string(token_id_str)
        token_fee = CustomFixedFee(
            amount=50,  
            denominating_token_id=denom_token_id,
            fee_collector_account_id=fee_collector_id,
            all_collectors_are_exempt=True
        )
        print("\n2. CustomFixedFee (Specific Token):")
        print(token_fee)
    except ValueError as e:
        print(f"Error creating token fee (using token ID '{token_id_str}'): {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


    # Example 3: Fee denominated in the token the fee is attached to (using 0.0.0 sentinel)
    try:
        same_token_fee = CustomFixedFee(
            amount=10,
            fee_collector_account_id=fee_collector_id
        )
        same_token_fee.set_denominating_token_to_same_token()
        print("\n3. CustomFixedFee (Same Token - Sentinel 0.0.0):")
        print(same_token_fee)
    except Exception as e:
        print(f"Error creating same-token fee: {e}")


    print("\n--- Example finished ---")

if __name__ == "__main__":
    main()