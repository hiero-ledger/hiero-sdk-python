"""
Run with:
uv run examples/tokens/custom_royalty_fee.py
python examples/tokens/custom_royalty_fee.py
"""

import os 
import sys
from dotenv import load_dotenv

from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()

def setup_client():
    """
    Initilise and set up the client with the operator account
    """
    
    network = Network(network_name)
    print(f"Connecting to the Hedera {network_name} network")
    client = Client(network)
    
    try:
        operator_id_str = os.getenv('OPERATOR_ID')
        operator_key_str = os.getenv('OPERATOR_KEY')

        if not operator_id_str or not operator_key_str:
            raise ValueError("Environment variables OPERATOR_ID or OPERATOR_KEY are missing.")

        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)

        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key
    
    except (TypeError, ValueError) as e:
        print(f"Error: {e}")
        print("Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

def custom_royalty_fee_example():
    """
    Demonstrates how to create a token with a custom Royalty fee.
    """
    
    client, operator_id, operator_key = setup_client()
    
    print("\n--- Creating Custom Royalty Fee ---")
    
    fallback_fee = CustomFixedFee(
        amount=Hbar(1).to_tinybars(),
        fee_collector_account_id=operator_id,
        all_collectors_are_exempt=False
    )
    
    royalty_fee = CustomRoyaltyFee(
        numerator=5, 
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=operator_id,
        all_collectors_are_exempt=False
    )
    
    print(f"Royalty Fee Configured: 5/100 (5%)")
    print(f"Fallback Fee: 1 HBAR")
    
    print(f"\n--- Creating Token with Royalty Fee ---")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Royalty NFT Collection")
        .set_token_symbol("RNFT")
        .set_treasury_account_id(operator_id)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE) 
        .set_decimals(0)                               
        .set_initial_supply(0)                        
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_custom_fees([royalty_fee]) 
        .freeze_with(client)
        .sign(operator_key)
    )
    
    try:
        # Execute the transaction
        receipt = transaction.execute(client)
        
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Transaction failed with status: {ResponseCode(receipt.status).name}")
            return

        token_id = receipt.token_id
        print(f"Token created successfully with ID: {token_id}")

        print("\n--- Verifying Fee on Network ---")
        token_info = TokenInfoQuery().set_token_id(token_id).execute(client)

        retrieved_fees = token_info.custom_fees
        if retrieved_fees:
            print(f"Success! Found {len(retrieved_fees)} custom fee(s) on token.")
            for fee in retrieved_fees:
                print(fee)
        else:
            print("Error: No custom fees found on the token.")

    except Exception as e:
        print(f"Transaction failed: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    custom_royalty_fee_example()