"""
Example demonstrating the validate_status feature for Transaction Receipts.

uv run examples/query/transaction_get_receipt_query_validate_status.py
python examples/query/transaction_get_receipt_query_validate_status.py
"""

import sys

from hiero_sdk_python import (
    AccountDeleteTransaction,
    AccountId,
    Client,
    ReceiptStatusError,
    ResponseCode,
    TransactionGetReceiptQuery,
)


def setup_client():
    """Initialize the Hiero client from environment variables."""
    try:
        client = Client.from_env()
        print(f"Client set up for {client.network.network}...")
        return client
    except ValueError as e:
        print(f"Error setting up client: {e}")
        sys.exit(1)


def submit_failing_transaction(client):
    """Submit a transaction designed to fail to demonstrate receipt handling."""
    tx = (
        AccountDeleteTransaction()
        .set_account_id(AccountId(0, 0, 9999999))
        .set_transfer_account_id(client.operator_account_id)
        .freeze_with(client)
    )

    # wait_for_receipt=False allows us to query the receipt manually later
    response = tx.execute(client, wait_for_receipt=False)

    print(f"Transaction submitted: {response.transaction_id}")

    return response.transaction_id


def run_manual_validation(client, transaction_id):
    """Demonstrate manual status checking (the default behavior)."""
    print("\n--- Option A: Manual Validation (Default) ---")
    query = TransactionGetReceiptQuery().set_transaction_id(transaction_id).set_validate_status(False)

    print("Executing query with validate_status=False")
    receipt = query.execute(client)
    status_name = ResponseCode(receipt.status).name
    print(f"Query returned receipt with status: {status_name}")


def run_automatic_validation(client, transaction_id):
    """Demonstrate automatic validation using ReceiptStatusError."""
    print("\n--- Option B: Automatic Validation ---")
    query = TransactionGetReceiptQuery().set_transaction_id(transaction_id).set_validate_status(True)

    try:
        print("Executing query with validate_status=True")
        query.execute(client)
    except ReceiptStatusError as e:
        status_name = ResponseCode(e.status).name
        print(f"Query raises expected exception: {status_name}")


def main():
    client = setup_client()

    # Get a transaction ID to query
    tx_id = submit_failing_transaction(client)

    # Default receipt query tx
    run_manual_validation(client, tx_id)

    # Receipt query with validate_status
    run_automatic_validation(client, tx_id)


if __name__ == "__main__":
    main()
