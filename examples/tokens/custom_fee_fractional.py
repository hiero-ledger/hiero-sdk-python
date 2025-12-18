"""
Run with:
uv run examples/tokens/custom_fractional_fee.py
python examples/tokens/custom_fractional_fee.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
)
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType


load_dotenv()


def setup_client():
    network_name = os.getenv("NETWORK", "testnet")

    # Validate environment variables
    if not os.getenv("OPERATOR_ID") or not os.getenv("OPERATOR_KEY"):
        print("❌ Missing OPERATOR_ID or OPERATOR_KEY in .env file.")
        sys.exit(1)

    try:
        network = Network(network_name)
        print(f"Connecting to Hedera {network_name} network!")
        client = Client(network)

        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

    except Exception as e:
        raise ConnectionError(f"Error initializing client: {e}") from e

    print(f"✅ Connected to Hedera {network_name} network as operator: {operator_id}")
    return client, operator_id, operator_key


def build_fractional_fee(operator_account: AccountId) -> CustomFractionalFee:
    """Creates a CustomFractionalFee instance."""
    return CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.INCLUSIVE,
        fee_collector_account_id=operator_account,
        all_collectors_are_exempt=True,
    )


def create_token_with_fee_key(client, operator_id, fractional_fee: CustomFractionalFee):
    """Create a fungible token with a fee_schedule_key."""
    print("Creating fungible token with fee_schedule_key...")
    fractional_fee = [fractional_fee]

    token_params = TokenParams(
        token_name="Fee Key Token",
        token_symbol="FKT",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.INFINITE,
        custom_fees=fractional_fee,
    )

    tx = TokenCreateTransaction(token_params=token_params)
    tx.freeze_with(client)
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Token created with ID: {token_id}")
    return token_id


def print_fractional_fees(token_info, fractional_fee):
    """Print all CustomFractionalFee objects from a TokenInfo."""
    if not token_info.custom_fees:
        print("No custom fees found.")
        return
    else:
        print("\n--- Custom Fractional Fee ---")
        print(fractional_fee)


def query_and_validate_fractional_fee(client: Client, token_id):
    """Fetch token info from Hedera and print the custom fractional fees."""
    print("\nQuerying token info to validate fractional fee...")
    token_info = TokenInfoQuery(token_id=token_id).execute(client)
    return token_info


def main():
    client, operator_id, _ = setup_client()
    # Build fractional fee
    fractional_fee = build_fractional_fee(operator_id)
    token_id = create_token_with_fee_key(client, operator_id, fractional_fee)

    # Query and validate fractional fee
    token_info = query_and_validate_fractional_fee(client, token_id)
    print_fractional_fees(token_info, fractional_fee)
    print("✅ Example completed successfully.")


if __name__ == "__main__":
    main()
