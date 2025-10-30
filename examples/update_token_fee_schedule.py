"""Example: Update Token Fee Schedule"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams, TokenKeys
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hbar import Hbar


def setup_client():
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

def create_token(client, operator_id, admin_key):
    print(" Creating token...")
    token_params = TokenParams(
        token_name="Fee Update Example Token",
        token_symbol="FUE",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.FINITE,
        max_supply=2000,
        custom_fees=[],
    )
    # We cannot add fee_schedule_key here yet due to TypeError
    keys = TokenKeys(admin_key=admin_key) 

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    tx.transaction_fee = Hbar(5).to_tinybars()
    tx.freeze_with(client).sign(admin_key)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f" Token creation failed: {ResponseCode(receipt.status).name}\n")
        client.close()
        sys.exit(1)

    token_id = receipt.token_id
    print(f" Token created successfully: {token_id}\n")
    return token_id


def update_fee_schedule(client, token_id, admin_key, operator_id):
    print(f" Updating fee schedule for token {token_id}...")
    new_fees = [
        CustomFixedFee(amount=150, fee_collector_account_id=operator_id),
        CustomRoyaltyFee(numerator=5, denominator=100, fee_collector_account_id=operator_id),
    ]
    print(f" Defined {len(new_fees)} custom fees.\n")
    tx = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(new_fees)
    )
    tx.transaction_fee = Hbar(5).to_tinybars()
    tx.freeze_with(client).sign(admin_key) 

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
        token_id = create_token(client, operator_id, operator_key)
        if token_id:
            update_fee_schedule(client, token_id, operator_key, operator_id)
    except Exception as e:
        print(f" Error during token operations: {e}")
    finally:
        client.close()
        print("\n Client closed. Example complete.")


if __name__ == "__main__":
    main()
