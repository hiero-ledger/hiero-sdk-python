#!/usr/bin/env python3
"""
Example demonstrating how to handle ReceiptStatusError in the Hiero SDK.

run:
uv run examples/errors/receipt_status_error.py
python examples/errors/receipt_status_error.py
"""
import os
import dotenv

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_associate_transaction import (
    TokenAssociateTransaction,
)
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.exceptions import ReceiptStatusError

dotenv.load_dotenv()


def main():
    # Initialize the client
    # For this example, we assume we are running against a local node or testnet
    # You would typically load these from environment variables
    operator_id_str = os.environ.get("OPERATOR_ID", "")
    operator_key_str = os.environ.get("OPERATOR_KEY", "")

    try:
        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)
    except Exception as e:
        print(f"Error parsing operator credentials: {e}")
        return

    client = Client()
    client.set_operator(operator_id, operator_key)

    # Create a  transaction that is likely to fail post-consensus
    # Here we try to associate a non-existent token

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
        # execute() submits the transaction to the network and returns a receipt
        # Note: this does NOT automatically raise an exception if the transaction fails post-consensus.
        receipt = transaction.execute(client)
        print(f"Transaction submitted. ID: {receipt.transaction_id}")

        # Check if the execution raised something other than SUCCESS
        # If not, we raise our custom ReceiptStatusError for handling.
        if receipt.status != ResponseCode.SUCCESS:
            raise ReceiptStatusError(receipt.status, receipt.transaction_id, receipt)
        # If we reach here, the transaction succeeded
        print("Transaction successful!")

    # This exception is raised when the transaction raised something other than SUCCESS
    except ReceiptStatusError as e:
        print("\nCaught ReceiptStatusError!")
        print(f"Status: {e.status} ({ResponseCode(e.status).name})")
        print(f"Transaction ID: {e.transaction_id}")
        print(
            "This error means the transaction reached consensus but failed logic execution."
        )

    # Catch all for unexpected errors
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
