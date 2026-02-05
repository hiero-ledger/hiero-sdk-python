#!/usr/bin/env python3
"""
Example demonstrating how to handle ReceiptStatusError in the Hiero SDK.

run:
uv run examples/errors/receipt_status_error.py
python examples/errors/receipt_status_error.py
"""
from hiero_sdk_python import (
    Client,
    ResponseCode,
    TokenAssociateTransaction,
    TokenId
)
from hiero_sdk_python.exceptions import ReceiptStatusError

def main() -> None:
    client = Client.from_env()
    
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    print("Creating transaction...")
    transaction = (
        TokenAssociateTransaction()
        .set_account_id(operator_id)
        .add_token_id(TokenId(0, 0, 3))
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        print("Executing transaction...")
        receipt = transaction.execute(client)
        print(f"Transaction submitted. ID: {receipt.transaction_id}")

        # Check if the execution raised something other than SUCCESS
        if receipt.status is None:
            raise ValueError("Receipt missing status")
        if receipt.status != ResponseCode.SUCCESS:
            raise ReceiptStatusError(receipt.status, receipt.transaction_id, receipt)

        print("Transaction successful!")

    # This exception is raised when the transaction raised something other than SUCCESS
    except ReceiptStatusError as e:
        print("\nCaught ReceiptStatusError!")
        print(f"Status: {e.status.name} ({e.status})")
        print(f"Transaction ID: {e.transaction_id}")
        print(
            "This error means the transaction reached consensus but failed logic execution."
        )

    # Catch all for unexpected errors
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()