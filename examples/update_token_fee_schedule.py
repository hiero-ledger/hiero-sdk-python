"""
Example: Update Token Fee Schedule
----------------------------------
Demonstrates creating a token, updating its custom fee schedule, and cleaning up.
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
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.tokens.custom_fee import CustomFixedFee, CustomRoyaltyFee


def setup_operator(client: Client):
    """Load operator credentials from .env and set them for the client."""
    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
        print(f"Operator set: {operator_id}\n")
        return operator_id, operator_key
    except Exception as e:
        print(f"Error setting up operator: {e}")
        sys.exit(1)


def create_token(client: Client, operator_id: AccountId, admin_key: PrivateKey):
    """Create a fungible token for the demo."""
    print("🚀 Creating token...")

    token_params = TokenParams(
        token_name="Fee Update Example Token",
        token_symbol="FUE",
        treasury_account_id=operator_id,
        initial_supply=1000,
        decimals=2,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.FINITE,
        max_supply=2000,
        custom_fees=[],  # initially no fees
    )
    keys = TokenKeys(admin_key=admin_key)

    tx = TokenCreateTransaction(token_params=token_params, keys=keys)
    tx.freeze_with(client).sign(admin_key)
    receipt = tx.execute(client)

    token_id = receipt.token_id
    if not token_id:
        raise RuntimeError("Token creation failed — no token ID returned.")

    print(f"Token created successfully: {token_id}\n")
    return token_id


def update_fee_schedule(client: Client, token_id, admin_key, operator_id):
    """Update the custom fee schedule for a given token."""
    print(f"Updating fee schedule for token {token_id}...")

    new_fees = [
        CustomFixedFee(amount=150, fee_collector_account_id=operator_id),
        CustomRoyaltyFee(numerator=5, denominator=100, fee_collector_account_id=operator_id),
    ]

    update_tx = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(new_fees)
    )

    update_tx.freeze_with(client).sign(admin_key)
    receipt = update_tx.execute(client)

    print(f"Fee schedule updated successfully! Status: {receipt.status.name}\n")


def delete_token(client: Client, token_id, admin_key):
    """Delete the created token to clean up."""
    print(f"🧹 Deleting token {token_id}...")
    delete_tx = TokenDeleteTransaction().set_token_id(token_id)
    delete_tx.freeze_with(client).sign(admin_key)
    receipt = delete_tx.execute(client)
    print(f" Token deletion status: {receipt.status.name}\n")


def main():
    """Main function: create a token, update its fee schedule, and delete it."""

    load_dotenv()

    # Use context manager to ensure proper cleanup
    with Client(Network(network="testnet")) as client:
        token_id_to_clean = None
        operator_id, operator_key = setup_operator(client)
        admin_key = operator_key

        try:
            # 1️⃣ Create token
            token_id = create_token(client, operator_id, admin_key)
            token_id_to_clean = token_id

            # 2️⃣ Update fee schedule
            update_fee_schedule(client, token_id, admin_key, operator_id)

        except Exception as e:
            print(f"Error during token operations: {e}")

        finally:
            # 3️⃣ Cleanup
            if token_id_to_clean:
                try:
                    delete_token(client, token_id_to_clean, admin_key)
                except Exception as e_del:
                    print(f"Failed to delete token: {e_del}")

        print("Client closed. Example complete.\n")


if __name__ == "__main__":
    main()
