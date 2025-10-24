"""
Example: Update Token Fee Schedule
Demonstrates creating a token, updating its custom fee schedule, and cleaning up.
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
from hiero_sdk_python.tokens.custom_fee import CustomFixedFee, CustomRoyaltyFee


def main():
    """Main function to create a token, update fee schedule, and delete it."""

    load_dotenv()
    client = Client(Network(network="testnet"))
    token_id_to_clean = None

    # --- 1. Set up Operator ---
    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
    except Exception as e:
        print(f"Error setting up operator: {e}")
        sys.exit(1)

    admin_key = operator_key
    print(f"Operator set. Using {operator_id} as admin key for example token.\n")

    try:
        # --- 2. Create a Token ---
        print("Creating token...")
        token_params = TokenParams(
            token_name="Fee Update Example Token",
            token_symbol="FUE",
            treasury_account_id=operator_id,
            initial_supply=1000,
            decimals=2,  # Realistic fungible token
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=2000,
            custom_fees=[]
        )
        keys = TokenKeys(admin_key=admin_key)

        create_tx = TokenCreateTransaction(token_params=token_params, keys=keys).freeze_with(client).sign(admin_key)
        create_receipt = create_tx.execute(client)
        token_id_to_update = create_receipt.token_id
        token_id_to_clean = token_id_to_update

        if not token_id_to_update:
            raise RuntimeError("Token creation failed, no token ID returned.")
        print(f"Token created successfully: {token_id_to_update}\n")

        # --- 3. Define new custom fees ---
        new_fees = [
            CustomFixedFee(amount=150, fee_collector_account_id=operator_id),
            CustomRoyaltyFee(numerator=5, denominator=100, fee_collector_account_id=operator_id),
        ]
        print(f"Defined {len(new_fees)} custom fees.\n")

        # --- 4. Update fee schedule ---
        print(f"Updating fee schedule for token {token_id_to_update}...")
        update_tx = TokenFeeScheduleUpdateTransaction().set_token_id(token_id_to_update).set_custom_fees(new_fees)
        update_tx.freeze_with(client).sign(admin_key)
        update_receipt = update_tx.execute(client)
        print(f"Fee schedule updated successfully! Status: {update_receipt.status.name}\n")

    except Exception as e:
        print(f"Error during token operations: {e}")

    finally:
        # --- 5. Clean up ---
        if token_id_to_clean:
            print(f"Deleting token {token_id_to_clean}...")
            try:
                delete_tx = TokenDeleteTransaction().set_token_id(token_id_to_clean).freeze_with(client).sign(admin_key)
                delete_receipt = delete_tx.execute(client)
                print(f"Token deletion status: {delete_receipt.status.name}")
            except Exception as e_del:
                print(f"Failed to delete token: {e_del}")

        client.close()
        print("\nClient closed. Example complete.")


if __name__ == "__main__":
    main()
