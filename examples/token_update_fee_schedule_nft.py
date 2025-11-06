"""Example: Update Custom Fees for an NFT"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams, TokenKeys
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.query.token_info_query import TokenInfoQuery


def setup_client():
    """Initialize client and operator credentials from .env."""
    load_dotenv()
    try:
        client = Client(Network(os.getenv("NETWORK", "testnet")))
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
        print(f" Operator set: {operator_id}\n")
        return client, operator_id, operator_key
    except Exception as e:
        print(f" Error setting up client: {e}")
        sys.exit(1)


def create_nft(client, operator_id, supply_key, fee_schedule_key):
    """Create an NFT with supply and fee schedule keys."""
    print(" Creating NFT...")
    token_params = TokenParams(
        token_name="NFT Fee Example",
        token_symbol="NFE",
        treasury_account_id=operator_id,
        initial_supply=0,
        decimals=0,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=SupplyType.FINITE,
        max_supply=1000,
        custom_fees=[], 
    )
    
    # A supply_key is REQUIRED for NFTs (to mint)
    # A fee_schedule_key is required to update fees
    keys = TokenKeys(
        supply_key=supply_key,
        fee_schedule_key=fee_schedule_key
    )

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    # tx.set_fee_schedule_key(fee_schedule_key)
    
    # Sign with the supply key as well
    tx.freeze_with(client).sign(supply_key)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f" Token creation failed: {ResponseCode(receipt.status).name}\n")
        client.close()
        sys.exit(1)

    token_id = receipt.token_id
    print(f" Token created successfully: {token_id}\n")
    return token_id


def update_custom_royalty_fee(client, token_id, fee_schedule_key, collector_account_id):
    """Updates the token's fee schedule with a new royalty fee."""
    print(f" Updating custom royalty fee for token {token_id}...")
    new_fees = [
        CustomRoyaltyFee(
            numerator=5, 
            denominator=100, # 5% royalty
            fee_collector_account_id=collector_account_id
        )
    ]
    print(f" Defined {len(new_fees)} new custom fees.\n")
    tx = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(new_fees)
    )
    
    tx.freeze_with(client).sign(fee_schedule_key) 

    try:
        receipt = tx.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(f" Fee schedule update failed: {ResponseCode(receipt.status).name}\n")
            sys.exit(1) 
        else:
            print(" Fee schedule updated successfully.\n")
    except Exception as e:
        print(f" Error during fee schedule update execution: {e}\n")
        sys.exit(1) 


def query_token_info(client, token_id):
    """Query token info and verify updated custom fees."""
    print(f"\nQuerying token info for {token_id}...\n")
    try:
        token_info = TokenInfoQuery(token_id=token_id).execute(client)
        print("Token Info Retrieved Successfully!\n")
        
        print(f"Name: {getattr(token_info, 'name', 'N/A')}")
        print(f"Symbol: {getattr(token_info, 'symbol', 'N/A')}")
        print(f"Total Supply: {getattr(token_info, 'total_supply', 'N/A')}")
        print(f"Treasury: {getattr(token_info, 'treasury_account_id', 'N/A')}")
        print(f"Decimals: {getattr(token_info, 'decimals', 'N/A')}")
        print(f"Max Supply: {getattr(token_info, 'max_supply', 'N/A')}")
        print()

        custom_fees = getattr(token_info, "custom_fees", [])
        if custom_fees:
            print(f"Found {len(custom_fees)} custom fee(s):")
            for i, fee in enumerate(custom_fees, 1):
                print(f"  Fee #{i}: {type(fee).__name__}")
                print(f"    Collector: {getattr(fee, 'fee_collector_account_id', 'N/A')}")
                if isinstance(fee, CustomRoyaltyFee):
                    print(f"    Royalty: {fee.numerator}/{fee.denominator}")
                else:
                    print(f"    Amount: {getattr(fee, 'amount', 'N/A')}")
        else:
            print("No custom fees defined for this token.\n")

    except Exception as e:
        print(f"Error querying token info: {e}")
        sys.exit(1) 

def main():
    client, operator_id, operator_key = setup_client()
    token_id = None
    try:
        # Use operator key as both supply and fee key
        supply_key = operator_key
        fee_key = operator_key
        
        token_id = create_nft(client, operator_id, supply_key, fee_key)
        
        if token_id:
            query_token_info(client, token_id) 
            update_custom_royalty_fee(client, token_id, fee_key, operator_id)
            query_token_info(client, token_id)
            
    except Exception as e:
        print(f" Error during token operations: {e}")
    finally:
        client.close()
        print("\n Client closed. Example complete.")


if __name__ == "__main__":
    main()
    
