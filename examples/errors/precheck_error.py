#!/usr/bin/env python3
"""
Example demonstrating how to handle PrecheckError in the Hiero SDK.

run:
uv run examples/errors/precheck_error.py
python examples/errors/precheck_error.py
"""

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python import (
    Client,
    TransferTransaction,
    AccountId
)

def main() -> None:
    # Initialize the client
    client = Client.from_env()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    print("Creating transaction with invalid parameters to force PrecheckError...")

    # Create a simple transfer transaction
    # To trigger a PrecheckError, we set the transaction valid duration to 0.
    # The node's precheck validation requires a valid duration, so this will fail immediately.
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -1)
        .add_hbar_transfer(AccountId(0, 0, 3), 1)
        .set_transaction_valid_duration(1) 
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        print("Executing transaction...")
        transaction.execute(client)
        print("Transaction unexpectedly succeeded (this should not happen).")

    except PrecheckError as e:
        print("\nCaught PrecheckError!")
        print(f"Status: {e.status.name} ({e.status})")
        print(f"Transaction ID: {e.transaction_id}")
        print("This error means the transaction failed validation at the node *before* reaching consensus.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()