"""
Run:
uv run examples/custom_fixed_fee.py
python examples/custom_fixed_fee.py

Example for creating a fungible token with a custom fixed fee.
"""

import os
import sys
from dotenv import load_dotenv
from typing import Tuple, List

# Hiero SDK imports
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TokenCreateTransaction,
    TokenInfoQuery,
    CustomFixedFee,
    Hbar,
    TokenId,
    TokenParams,
    TokenKeys
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType, ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fee import CustomFee

# Load environment variables from .env file
load_dotenv()

def setup_client() -> Tuple[Client, AccountId, PrivateKey]:
    """
    Sets up and configures the Hiero client from environment variables.
    (Consistent with other example files)
    """
    try:
        network = Network(os.getenv('NETWORK'))
        client = Client(network)

        operator_id_str = os.getenv('OPERATOR_ID')
        operator_key_str = os.getenv('OPERATOR_KEY')

        if not operator_id_str or not operator_key_str:
            print("Error: OPERATOR_ID or OPERATOR_KEY not found in .env file.")
            sys.exit(1)

        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)
        client.set_operator(operator_id, operator_key)
        
        return client, operator_id, operator_key

    except (TypeError, ValueError, Exception) as e:
        print(f"Error: Client setup failed. {e}")
        sys.exit(1)

def define_custom_fee(collector_id: AccountId) -> CustomFixedFee:
    """
    Defines and prints a CustomFixedFee object.
    This will use the __repr__ method added in the previous issue.
    """
    print("\nStep 1: Define the Custom Fixed Fee")
    
    fee = CustomFixedFee(
        amount=Hbar(1.5).to_tinybars(),
        denominating_token_id=None,
        fee_collector_account_id=collector_id
    )

    print(f"Fee object created: {fee}")
    return fee

def create_token_with_fee(
    client: Client, 
    operator_id: AccountId, 
    admin_key: PrivateKey, 
    custom_fees: List[CustomFee]
) -> TokenId:
    """
    Creates a new fungible token that includes a custom fee schedule.
    (Based on 'create_fungible_token' from other examples)
    """
    print(f"\nStep 2: Create a new fungible token with this fee...")

    treasury_key = client.operator_private_key 
    
    try:

        token_params = TokenParams(
            token_name="My Token with Fixed Fee",
            token_symbol="H-FEE",
            decimals=2,
            initial_supply=10000, 
            treasury_account_id=operator_id,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=100000,
            custom_fees=custom_fees 
        )
        token_keys = TokenKeys(
            admin_key=admin_key
        )

        receipt = (
            TokenCreateTransaction(
                token_params=token_params,
                keys=token_keys
            )
            .freeze_with(client)
            .sign(treasury_key)
            .sign(admin_key) 
            .execute(client)
        )
        
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Token creation failed: {ResponseCode.get_name(receipt.status)}")
            sys.exit(1)

        token_id = receipt.token_id
        print(f"Successfully created token: {token_id}")
        return token_id

    except Exception as e:
        print(f"Error during token creation: {e}")
        sys.exit(1)

def query_token_and_check_fee(client: Client, token_id: TokenId):
    """
    Queries the network for the token's information to verify its properties.
    (Based on 'get_token_info' from other examples)
    """
    print(f"\nStep 3: Querying token {token_id} to verify fees...")
    try:
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(client)
        )
        
        print("Query successful.")

        if info.custom_fees:
            print(f"\nVerified custom fees on token (using __repr__):")
            for fee in info.custom_fees:
                print(f"- {fee}")

                if isinstance(fee, CustomFixedFee):
                    print(f"  (Fee found: {fee.amount} tinybars)")
        else:
            print("\nWarning: Token info returned no custom fees.")
            
    except Exception as e:
        print(f"Error during token info query: {e}")
        sys.exit(1)

def main():
    """
    Main e2e workflow:
    1. Set up the client.
    2. Define a custom fixed fee.
    3. Create a token with that fee.
    4. Query the token to verify the fee was set.
    """
    print("--- Starting Custom Fixed Fee e2e Example ---")
    
    setup_result = setup_client()
    if setup_result is None:
        sys.exit(1)
        
    client, operator_id, operator_key = setup_result
    
    # For this example, we'll use the operator key as the token admin key
    admin_key = operator_key 
    
    # 1. Define the fee
    fee = define_custom_fee(operator_id)
    
    # 2. Create token with the fee
    token_id = create_token_with_fee(client, operator_id, admin_key, [fee])
    
    # 3. Query token to verify
    query_token_and_check_fee(client, token_id)
    
    print("\n--- Example finished ---")

if __name__ == "__main__":
    main()