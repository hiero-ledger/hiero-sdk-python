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
from hiero_sdk_python.hbar import Hbar


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


def create_nft(client, operator_id, admin_key, fee_schedule_key):
    """Create an NFT with an admin key and fee schedule key."""
    print(" Creating NFT...")
    token_params = TokenParams(
        token_name="NFT Fee Example",
        token_symbol="NFE",
        treasury_account_id=operator_id,
        initial_supply=0, # NFTs have 0 initial supply
        decimals=0, # NFTs must have 0 decimals
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=SupplyType.FINITE,
        max_supply=1000,
        custom_fees=[], # No custom fees at creation
    )
    
    # fee_schedule_key is required to be able to update custom fees later
    keys = TokenKeys(
        admin_key=admin_key,
        supply_key=admin_key, # Need a supply key to mint
        fee_schedule_key=fee_schedule_key
    )

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    # Token creation must be signed by the admin key (if set) and treasury key (operator)
    tx.freeze_with(client).sign(admin_key) 
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
        # NFTs can have royalty fees
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
    
    # The transaction MUST be signed by the fee_schedule_key
    tx.freeze_with(client).sign(fee_schedule_key) 

    try:
        receipt = tx.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(f" Fee schedule update failed: {ResponseCode(receipt.status).name}\n")
        else:
            print(" Fee schedule updated successfully.\n")
    except Exception as e:
        print(f" Error during fee schedule update execution: {e}\n")


def main():
    client, operator_id, operator_key = setup_client()
    token_id = None
    try:
        admin_key = operator_key
        fee_key = operator_key
        
        token_id = create_nft(client, operator_id, admin_key, fee_key)
        
        if token_id:
            update_custom_royalty_fee(client, token_id, fee_key, operator_id)
            
    except Exception as e:
        print(f" Error during token operations: {e}")
    finally:
        client.close()
        print("\n Client closed. Example complete.")


if __name__ == "__main__":
    main()