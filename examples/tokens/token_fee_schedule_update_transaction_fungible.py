"""Example: Update Custom Fees for a Fungible Token
uv run examples/tokens/token_fee_schedule_update_transaction_fungible.py
python examples/tokens/token_fee_schedule_update_transaction_fungible.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import Client, AccountId, PrivateKey, Network
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


def setup_client():
    """Initialize client and operator credentials from .env."""
    load_dotenv()
    network_name = os.getenv("NETWORK", "testnet").lower()

    try:
        network = Network(network_name)
        print(f"Connecting to Hedera {network_name} network!")
        client = Client(network)
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
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
        custom_fees=[],  # No custom fees at creation
    )

    keys = TokenKeys(fee_schedule_key=fee_schedule_key)

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)

    tx.freeze_with(client)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f" Token creation failed: {ResponseCode(receipt.status).name}\n")
        client.close()
        sys.exit(1)

    token_id = receipt.token_id
    print(f" Token created successfully: {token_id}\n")
    return token_id


def update_custom_fixed_fee(client, token_id, fee_schedule_key, treasury_account_id):
    """Updates the token's fee schedule with a new fixed fee."""
    print(f" Updating custom fixed fee for token {token_id}...")
    new_fees = [
        # Send the custom fee to the token's treasury account
        CustomFixedFee(amount=150, fee_collector_account_id=treasury_account_id)
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
            sys.exit(1)
        else:
            print(" Fee schedule updated successfully.\n")
    except Exception as e:
        print(f" Error during fee schedule update execution: {e}\n")
        sys.exit(1)


def query_token_info(client, token_id):
    """Query token info to show the custom fees."""
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
                print(
                    f"    Collector: {getattr(fee, 'fee_collector_account_id', 'N/A')}"
                )
                if isinstance(fee, CustomFixedFee):
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
        fee_key = operator_key

        token_id = create_fungible_token(client, operator_id, fee_key)

        if token_id:
            query_token_info(client, token_id)
            # Pass the operator_id as the fee collector (which is also the treasury)
            update_custom_fixed_fee(client, token_id, fee_key, operator_id)
            query_token_info(client, token_id)

    except Exception as e:
        print(f" Error during token operations: {e}")
    finally:
        client.close()
        print("\n Client closed. Example complete.")


if __name__ == "__main__":
    main()
