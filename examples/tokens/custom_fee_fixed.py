"""
Run with:
uv run examples/tokens/custom_fixed_fee.py
python examples/tokens/custom_fixed_fee.py
"""

import sys

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def custom_fixed_fee_example():
    """

    Demonstrates how to create a token with a Custom Fixed Fee.

    """

    client = setup_client()

    print("\n--- Creating Custom Fixed Fee ---")

    fixed_fee = CustomFixedFee(
        amount=Hbar(1).to_tinybars(),
        fee_collector_account_id=client.operator_account_id,
        all_collectors_are_exempt=False,
    )

    print(f"Fee Definition: Pay 1 HBAR to {client.operator_account_id}")

    print("\n--- Creating Token with Fee ---")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Fixed Fee Example Token")
        .set_token_symbol("FFET")
        .set_decimals(2)
        .set_treasury_account_id(client.operator_account_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_initial_supply(1000)
        .set_admin_key(client.operator_private_key)
        .set_custom_fees([fixed_fee])
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    try:
        receipt = transaction.execute(client)

        # Check if the status is explicitly SUCCESS
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"Transaction failed with status: {ResponseCode(receipt.status).name}"
            )

        token_id = receipt.token_id
        print(f"Token created successfully with ID: {token_id}")

        print("\n--- Verifying Fee on Network ---")
        token_info = TokenInfoQuery().set_token_id(token_id).execute(client)

        retrieved_fees = token_info.custom_fees
        if retrieved_fees:
            print(f"Success! Found {len(retrieved_fees)} custom fee(s) on token.")
            for fee in retrieved_fees:
                print(f"Fee Collector: {fee.fee_collector_account_id}")
                print(f"Fee Details: {fee}")
        else:
            print("Error: No custom fees found on the token.")

    except Exception as e:
        print(f"Transaction failed: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    custom_fixed_fee_example()
