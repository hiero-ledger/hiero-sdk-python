#!/usr/bin/env python3
"""
Example demonstrating how to handle MaxAttemptsError in the Hiero SDK.

run:
uv run examples/errors/max_attempts_error.py
python examples/errors/max_attempts_error.py
"""

from hiero_sdk_python import (
    Client,
    TransactionGetReceiptQuery,
    TransactionId,
)
from hiero_sdk_python.exceptions import MaxAttemptsError

def main() -> None:
    # Initialize the client
    client = Client.from_env()
    operator_id = client.operator_account_id

    # Configure client to fail quickly
    # This sets the maximum number of attempts for any request to 1
    client.set_max_attempts(1)

    print("Attempting to fetch receipt with restricted max attempts...")

    # We generate a random transaction ID that definitely doesn't exist.
    # The network would normally return RECEIPT_NOT_FOUND, but depending on the
    # node's state or if we simulate a network blip, the SDK's retry mechanism kicks in.
    # By forcing max_attempts=1, we prevent retries.
    # Note: Triggering a pure MaxAttemptsError usually requires a timeout or busy node.
    # This example demonstrates the structure of handling the error.
    

    # Using a generated TransactionId
    tx_id = TransactionId.generate(operator_id)

    try:
        TransactionGetReceiptQuery().set_transaction_id(tx_id).execute(client)
        print("Query finished (unexpected for this example test).")

    except MaxAttemptsError as e:
        print("\nCaught MaxAttemptsError!")
        print(f"Node ID: {e.node_id}")
        print(f"Message: {e.message}")
        print("This error means the SDK gave up after reaching the maximum number of retry attempts.")
        
    except Exception as e:
        # Note: In a real network test with a made-up ID, we might get ReceiptStatusError 
        # or PrecheckError (RECEIPT_NOT_FOUND). MaxAttemptsError typically happens 
        # on network timeouts or BUSY responses.
        print(f"\nCaught unexpected error (expected for this specific simulation): {type(e).__name__}")
        print(f"Details: {e}")
        print("\n(To verify MaxAttemptsError logic, this example relies on the client's retry configuration)")


if __name__ == "__main__":
    main()