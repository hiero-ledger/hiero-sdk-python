"""
This is a simple example of how to update a token's fee schedule.

It:
1. Loads environment variables.
2. Sets up a client.
3. Defines a new custom fee schedule.
4. Builds and executes the TokenFeeScheduleUpdateTransaction.
5. Prints the receipt status.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY (mandatory)
- TOKEN_ID_TO_UPDATE (mandatory, e.g., "0.0.12345")
- TOKEN_ADMIN_KEY (mandatory, the private key for the token's admin key)

Usage:
uv run examples/update_token_fee_schedule.py
python examples/update_token_fee_schedule.py
"""

import os
import sys
from dotenv import load_dotenv

# --- Imports for Client Setup (from token_create_fungible_finite.py) ---
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)

# --- Imports for your new feature ---
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.custom_fee import (
    CustomFixedFee,
    CustomRoyaltyFee,
)
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)


def main():
    """Main function to update a token's fee schedule."""
    
    # --- 1. Set up Client (Pattern from token_create_fungible_finite.py) ---
    load_dotenv()
    network = Network(network="testnet")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
    except Exception as e:
        print(f"Error setting up client: {e}")
        print("Please check your OPERATOR_ID and OPERATOR_KEY in .env file.")
        sys.exit(1)

    # --- 2. Load the required variables from .env ---
    # These are the variables the *user* must provide.
    token_id_str = os.getenv("TOKEN_ID_TO_UPDATE")
    admin_key_str = os.getenv("TOKEN_ADMIN_KEY")

    if not token_id_str or not admin_key_str:
        print("Error: TOKEN_ID_TO_UPDATE and TOKEN_ADMIN_KEY must be set in .env")
        sys.exit(1)

    try:
        token_to_update = TokenId.from_string(token_id_str)
        admin_key = PrivateKey.from_string(admin_key_str)
    except Exception as e:
        print(f"Error parsing token ID or admin key: {e}")
        sys.exit(1)

    print(f"Attempting to update fee schedule for token: {token_to_update}")

    # --- 3. Define the *new* custom fee schedule ---
    # (Pattern from custom_fee.py)
    new_fee_list = [
        CustomFixedFee(
            amount=150,  # 150 tinybar
            fee_collector_account_id=operator_id,
        ),
        CustomRoyaltyFee(
            numerator=5,  # 5% royalty
            denominator=100,
            fee_collector_account_id=operator_id,
        ),
    ]
    print(f"New fee schedule will have {len(new_fee_list)} custom fees.")

    # --- 4. Build and execute your new transaction ---
    try:
        transaction = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_to_update)
            .set_custom_fees(new_fee_list)
            .freeze_with(client)
            .sign(admin_key)  # The token's Admin Key MUST sign
        )

        receipt = transaction.execute(client)
        print(f"Transaction successful with status: {receipt.status.name}")

    except Exception as e:
        print(f"Transaction failed: {str(e)}")
        sys.exit(1)
    finally:
        # --- 5. Close the client (Pattern from token_create_fungible_finite.py) ---
        client.close()


if __name__ == "__main__":
    main()