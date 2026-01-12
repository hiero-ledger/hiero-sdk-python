"""
uv run examples/tokens/token_create_transaction_token_fee_schedule_key.py

Example: Demonstrating the fee_schedule_key in Token Creation

This example shows the role of the fee_schedule_key when creating a token:
- With fee_schedule_key: Allows updating custom fees after token creation.
- Without fee_schedule_key: Custom fees are fixed and immutable.

It creates two fungible tokens:
1. One with a fee_schedule_key (fees can be updated).
2. One without a fee_schedule_key (fees cannot be updated).

Then, it attempts to update the custom fees for both tokens to demonstrate the difference.
"""

import sys

from hiero_sdk_python import Client, PrivateKey
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.query.token_info_query import TokenInfoQuery

# Load environment variables


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def create_token_with_fee_key(client, operator_id):
    """Create a fungible token with a fee_schedule_key."""
    print("Creating fungible token with fee_schedule_key...")
    fee_schedule_key = PrivateKey.generate_ed25519()
    initial_fees = [CustomFixedFee(amount=100, fee_collector_account_id=operator_id)]

    token_params = TokenParams(
        token_name="Fee Key Token",
        token_symbol="FKT",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.INFINITE,
        custom_fees=initial_fees,
    )

    keys = TokenKeys(fee_schedule_key=fee_schedule_key)

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    tx.freeze_with(client)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Token created with ID: {token_id} (has fee_schedule_key)")
    return token_id, fee_schedule_key


def create_token_without_fee_key(client, operator_id):
    """Create a fungible token without a fee_schedule_key."""
    print("Creating fungible token without fee_schedule_key...")
    initial_fees = [CustomFixedFee(amount=100, fee_collector_account_id=operator_id)]

    token_params = TokenParams(
        token_name="No Fee Key Token",
        token_symbol="NFKT",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.INFINITE,
        custom_fees=initial_fees,
    )

    # No keys set, so no fee_schedule_key
    tx = TokenCreateTransaction(token_params=token_params)
    tx.freeze_with(client)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Token created with ID: {token_id} (no fee_schedule_key)")
    return token_id


def query_token_fees(client, token_id, description):
    """Query and display the custom fees for a token."""
    token_info = TokenInfoQuery(token_id=token_id).execute(client)
    fees = token_info.custom_fees
    print(f"{description} - Custom fees: {len(fees)} fee(s)")
    for fee in fees:
        print(f"  - Fixed fee: {fee.amount} to {fee.fee_collector_account_id}")


def attempt_fee_update(client, token_id, fee_schedule_key, description):
    """Attempt to update custom fees for a token."""
    print(f"\nAttempting to update fees for {description}...")
    new_fees = [
        CustomFixedFee(amount=200, fee_collector_account_id=client.operator_account_id)
    ]

    tx = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(new_fees)
    )

    if fee_schedule_key:
        tx.freeze_with(client).sign(fee_schedule_key)

    try:
        receipt = tx.execute(client)
        if receipt.status == ResponseCode.SUCCESS:
            print("Fee update succeeded.")
        else:
            print(f"Fee update failed: {ResponseCode(receipt.status).name}")
    except Exception as e:
        print(f"Fee update failed with exception: {e}")


def main():

    client = setup_client()
    operator_id = client.operator_account_id

    try:
        # Create token with fee_schedule_key
        token_with_key, fee_key = create_token_with_fee_key(client, operator_id)
        query_token_fees(
            client, token_with_key, "Token with fee_schedule_key (initial)"
        )

        # Create token without fee_schedule_key
        token_without_key = create_token_without_fee_key(client, operator_id)
        query_token_fees(
            client, token_without_key, "Token without fee_schedule_key (initial)"
        )

        # Attempt updates
        attempt_fee_update(
            client, token_with_key, fee_key, "token with fee_schedule_key"
        )
        attempt_fee_update(
            client, token_without_key, None, "token without fee_schedule_key"
        )

        # Query final fees
        query_token_fees(
            client, token_with_key, "Token with fee_schedule_key (after update)"
        )
        query_token_fees(
            client, token_without_key, "Token without fee_schedule_key (after update)"
        )

    except Exception as e:
        print(f"Error during operations: {e}")
    finally:
        client.close()
        print("\nClient closed. Example complete.")


if __name__ == "__main__":
    main()
