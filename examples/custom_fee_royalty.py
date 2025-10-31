"""
End-to-end example for creating a Non-Fungible Token (NFT)
with a custom royalty fee on the Hedera testnet.
"""

import os
from dotenv import load_dotenv
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.custom_fees.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.token.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.token.token_info_query import TokenInfoQuery
from hiero_sdk_python.token.token_type import TokenType
from hiero_sdk_python.token.token_supply_type import TokenSupplyType
from hiero_sdk_python.key.key import Key
from hiero_sdk_python.hbar.hbar import Hbar

def set_up_client() -> Client:
    """
    Sets up and returns the Hedera client.
    (Copied from other examples for consistency)
    """
    load_dotenv()
    try:
        operator_id_str = os.environ["OPERATOR_ID"]
        operator_key_str = os.environ["OPERATOR_KEY"]
    except KeyError:
        raise Exception("OPERATOR_ID and OPERATOR_KEY env variables must be set")

    client = Client.for_testnet()
    client.set_operator(AccountId.from_string(operator_id_str), Key.from_string(operator_key_str))
    return client

def create_token_with_fee(client: Client, fee: CustomRoyaltyFee) -> AccountId:
    """
    Creates a new Non-Fungible Token (NFT) with a custom royalty fee.
    Royalty fees can only be applied to NON_FUNGIBLE_UNIQUE token types.
    """
    print("Creating a new NFT with a custom royalty fee...")
    
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    # Create the TokenCreateTransaction
    tx = TokenCreateTransaction(
        token_name="My Royalty NFT",
        token_symbol="MRNFT",
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=TokenSupplyType.FINITE,
        treasury_account_id=operator_id,
        # Add the custom fee we defined
        custom_fees=[fee],
        admin_key=operator_key,
        supply_key=operator_key,
        max_supply=100,
        # Set transaction fee
        max_transaction_fee=Hbar(30) 
    )

    # Sign and execute
    submitted_tx = tx.execute(client)
    receipt = submitted_tx.get_receipt(client)
    token_id = receipt.token_id

    print(f"Successfully created token with ID: {token_id}")
    return token_id

def query_token(client: Client, token_id: AccountId):
    """
    Queries the token info to verify the custom fee.
    """
    print(f"\nQuerying token {token_id} for custom fee verification...")
    
    token_info = TokenInfoQuery().set_token_id(token_id).execute(client)
    
    print(f"Found {len(token_info.custom_fees)} custom fees.")
    
    if token_info.custom_fees:
        # Access the first fee (we only added one)
        fee = token_info.custom_fees[0]
        if isinstance(fee, CustomRoyaltyFee):
            print("Verified: CustomRoyaltyFee found.")
            print(f"  Numerator: {fee.numerator}")
            print(f"  Denominator: {fee.denominator}")
            print(f"  Fee Collector: {fee.fee_collector_account_id}")
        else:
            print(f"Verified: Found a fee, but it's not a Royalty Fee. Type: {type(fee)}")
    else:
        print("Error: No custom fees found on the token.")

def main():
    """
    Main function to orchestrate the end-to-end example.
    """
    client = set_up_client()
    operator_id = client.operator_account_id
    
    
    # This will be a 10/100 (10%) royalty fee, paid to the operator's account
    royalty_fee = CustomRoyaltyFee(
        numerator=10,
        denominator=100,
        fallback_fee=None, # No fallback fee for this example
        fee_collector_account_id=operator_id
    )
    
    try:
        
        token_id = create_token_with_fee(client, royalty_fee)
        
        
        query_token(client, token_id)
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()