"""
Run with:
uv run examples/tokens/custom_royalty_fee.py
python examples/tokens/custom_royalty_fee.py
"""

import sys

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_royalty_fee_object(client):
    """Creates the CustomRoyaltyFee object with a fallback fee."""
    fallback_fee = CustomFixedFee(
        amount=Hbar(1).to_tinybars(),
        fee_collector_account_id=client.operator_account_id,
        all_collectors_are_exempt=False,
    )

    royalty_fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=client.operator_account_id,
        all_collectors_are_exempt=False,
    )
    print(f"Royalty Fee Configured: {royalty_fee.numerator}/{royalty_fee.denominator}")
    print(f"Fallback Fee: {Hbar.from_tinybars(fallback_fee.amount)} HBAR")
    return royalty_fee


def create_token_with_fee(client, royalty_fee):
    """Creates a token with the specified royalty fee attached."""

    print("\n--- Creating Token with Royalty Fee ---")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Royalty NFT Collection")
        .set_token_symbol("RNFT")
        .set_treasury_account_id(client.operator_account_id)
        .set_admin_key(client.operator_private_key)
        .set_supply_key(client.operator_private_key)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_decimals(0)
        .set_initial_supply(0)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_custom_fees([royalty_fee])
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        raise RuntimeError(
            f"Token creation failed: {ResponseCode(receipt.status).name}"
        )

    token_id = receipt.token_id
    print(f"Token created successfully with ID: {token_id}")
    return token_id


def verify_token_fee(client, token_id):
    """Queries the network to verify the fee exists."""

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


def main():
    """Main execution flow."""
    client = setup_client()

    with client:
        try:
            royalty_fee = create_royalty_fee_object(client)
            token_id = create_token_with_fee(client, royalty_fee)
            verify_token_fee(client, token_id)
        except Exception as e:
            print(f"Execution failed: {e}")


if __name__ == "__main__":
    main()
