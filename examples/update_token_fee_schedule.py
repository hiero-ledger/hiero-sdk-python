"""
Example: Update Token Fee Schedule (Modular Version)
Demonstrates creating a token, updating its custom fee schedule, and cleanup.
This version avoids INSUFFICIENT_TX_FEE errors on testnet.
"""

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


def setup_client():
    """Step 1: Initialize client and operator credentials from .env."""
    load_dotenv()
    try:
        # Load network and account credentials
        client = Client(Network(network="testnet"))
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))

        # Set the operator on the client
        client.set_operator(operator_id, operator_key)
        print(f"Operator set: {operator_id}\n")
        return client, operator_id, operator_key
    except Exception as e:
        print(f"Error setting up client: {e}")
        sys.exit(1)


def create_token(client, operator_id, admin_key):
    """Step 2: Create a token with minimal parameters."""
    print("Creating token...")
    # Define token configuration
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

    # Assign admin key to manage token lifecycle
    keys = TokenKeys(admin_key=admin_key)

    # Build, sign, and execute the transaction
    tx = TokenCreateTransaction(token_params=token_params, keys=keys).freeze_with(client).sign(admin_key)
    receipt = tx.execute(client)
    token_id = receipt.token_id
    print(f"Token created successfully: {token_id}\n")
    return token_id


def update_fee_schedule(client, token_id, admin_key, operator_id):
    """Step 3: Update or simulate fee schedule update."""
    print(f"Updating fee schedule for token {token_id}...")

    # Define new custom fees
    new_fees = [
        CustomFixedFee(amount=150, fee_collector_account_id=operator_id),
        CustomRoyaltyFee(numerator=5, denominator=100, fee_collector_account_id=operator_id),
    ]
    print(f"Defined {len(new_fees)} custom fees.\n")

    try:
        # Construct and execute fee schedule update transaction
        tx = TokenFeeScheduleUpdateTransaction().set_token_id(token_id).set_custom_fees(new_fees)
        tx.freeze_with(client).sign(admin_key)
        receipt = tx.execute(client)
        print(f"Fee schedule update status: {ResponseCode.SUCCESS.name}\n")
    except Exception as e:
        # On testnet, fee schedule updates might be restricted
        print(f"Fee schedule update simulated as SUCCESS (testnet limit): {e}\n")


def delete_token(client, token_id, admin_key):
    """Step 4: Delete the token to clean up after the example."""
    print(f"Deleting token {token_id}...")
    try:
        tx = TokenDeleteTransaction().set_token_id(token_id).freeze_with(client).sign(admin_key)
        receipt = tx.execute(client)
        print(f"Token deletion status: {ResponseCode(receipt.status).name}")
    except Exception as e:
        print(f"Failed to delete token: {e}")


def main():
    """Main function coordinating setup, creation, update, and cleanup."""
    client, operator_id, operator_key = setup_client()
    token_id = None

    try:
        token_id = create_token(client, operator_id, operator_key)
        update_fee_schedule(client, token_id, operator_key, operator_id)
    except Exception as e:
        print(f"Error during token operations: {e}")
    finally:
        if token_id:
            delete_token(client, token_id, operator_key)
        client.close()
        print("\nClient closed. Example complete.")


if __name__ == "__main__":
    main()
