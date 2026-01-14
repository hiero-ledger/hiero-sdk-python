"""
uv run examples/query/transaction_get_receipt_query.py
python examples/query/transaction_get_receipt_query.py
"""

import sys

from hiero_sdk_python import (
    Client,
    TransferTransaction,
    Hbar,
    TransactionGetReceiptQuery,
    ResponseCode,
    AccountCreateTransaction,
    PrivateKey,
)


def create_account(client):
    """Create a new recipient account"""
    print("\nSTEP 1: Creating a new recipient account...")

    operator_key = client.operator_private_key
    if operator_key is None:
        raise ValueError("Operator private key not set in environment")

    recipient_key = PrivateKey.generate()

    try:
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
            .freeze_with(client)
            .sign(operator_key)
        )

        receipt = tx.execute(client)
        recipient_id = receipt.account_id

        print(f"Success! Created a new recipient account with ID: {recipient_id}")
        return recipient_id

    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def _print_receipt_children(queried_receipt):
    """Pretty-print receipt status and any child receipts."""
    children = queried_receipt.children

    if not children:
        print("No child receipts returned.")
        return

    print(f"Child receipts count: {len(children)}")
    for idx, child in enumerate(children, start=1):
        print(f"  {idx}. status={ResponseCode(child.status).name}")


def _print_receipt_duplicates(queried_receipt):
    """Pretty-print receipt status and any duplicate receipts."""
    duplicates = queried_receipt.duplicates

    if not duplicates:
        print("No duplicate receipts returned.")
        return

    print(f"Duplicate receipts count: {len(duplicates)}")
    for idx, duplicate in enumerate(duplicates, start=1):
        print(f"  {idx}. status={ResponseCode(duplicate.status).name}")


def query_receipt():
    """
    Demonstrates:
    - account creation
    - HBAR transfer
    - querying transaction receipt (children + duplicates)
    """
    # Configure client from environment
    client = Client.from_env()

    if client.operator_account_id is None:
        raise ValueError("OPERATOR_ID must be set in environment")

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    print(f"Operator: {operator_id}")

    # Create recipient account
    recipient_id = create_account(client)

    # Transfer HBAR
    print("\nSTEP 2: Transferring HBAR...")
    amount = Hbar(10)

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -amount.to_tinybars())
        .add_hbar_transfer(recipient_id, amount.to_tinybars())
        .freeze_with(client)
        .sign(operator_key)
    )

    receipt = transaction.execute(client)
    transaction_id = transaction.transaction_id

    print(f"Transaction ID: {transaction_id}")
    print(f"Transfer status: {ResponseCode(receipt.status).name}")

    # Query transaction receipt
    print("\nSTEP 3: Querying transaction receipt...")
    receipt_query = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transaction_id)
        .set_include_children(True)
        .set_include_duplicates(True)
    )

    queried_receipt = receipt_query.execute(client)
    print(
        f"Queried transaction status: {ResponseCode(queried_receipt.status).name}"
    )

    _print_receipt_children(queried_receipt)
    _print_receipt_duplicates(queried_receipt)


if __name__ == "__main__":
    query_receipt()
