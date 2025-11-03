"""Example: Update Custom Fees for a Fungible Token"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams, TokenKeys
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.response_code import ResponseCode


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


def create_fungible_token(client, operator_id, fee_schedule_key):
    """Create a fungible token with only a fee schedule key."""
    print(" Creating fungible token...")
    token_params = TokenParams(
        token_name="Fungible Fee Example",
        token_symbol="FFE",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.FINITE,
        max_supply=2000,
        custom_fees=[], # No custom fees at creation
    )
    
    #  Admin key is not required.
    # fee_schedule_key is required to be able to update custom fees later
    keys = TokenKeys(
        fee_schedule_key=fee_schedule_key
    )

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    # Use the setter as well
    tx.set_fee_schedule_key(fee_schedule_key)
    
    # Token creation is signed by the treasury key (operator)
    tx.freeze_with(client)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f" Token creation failed: {ResponseCode(receipt.status).name}\n")
        client.close()
        sys.exit(1)

    token_id = receipt.token_id
    print(f" Token created successfully: {token_id}\n")
    return token_id


def update_custom_fixed_fee(client, token_id, fee_schedule_key, collector_account_id):
    """Updates the token's fee schedule with a new fixed fee."""
    print(f" Updating custom fixed fee for token {token_id}...")
    new_fees = [
        CustomFixedFee(amount=150, fee_collector_account_id=collector_account_id)
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
        # For this example, we only need a fee schedule key
        fee_key = operator_key
        
        token_id = create_fungible_token(client, operator_id, fee_key)
        
        if token_id:
            update_custom_fixed_fee(client, token_id, fee_key, operator_id)
            
    except Exception as e:
        print(f" Error during token operations: {e}")
    finally:
        client.close()
        print("\n Client closed. Example complete.")


if __name__ == "__main__":
    main()
