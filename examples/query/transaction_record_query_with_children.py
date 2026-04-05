"""
Example demonstrating transaction record query with child records.

To run the example run:
- uv run examples/query/transaction_record_query_with_children.py
- python examples/query/transaction_record_query_with_children.py
"""

import sys

from hiero_sdk_python import (
    AccountId,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
    TransactionRecordQuery,
    TransferTransaction,
)


def submit_alias_auto_create_transfer(client):
    """Transfer HBAR to a fresh EVM alias to trigger auto-account creation."""
    try:
        alias_key = PrivateKey.generate_ecdsa()
        alias_account_id = AccountId.from_evm_address(alias_key.public_key().to_evm_address(), 0, 0)

        transaction = (
            TransferTransaction()
            .add_hbar_transfer(alias_account_id, Hbar(1).to_tinybars())
            .add_hbar_transfer(client.operator_account_id, Hbar(-1).to_tinybars())
        )
        transaction.execute(client)

        return transaction.transaction_id
    except Exception as e:
        print(f"Error submitting alias auto-create transfer: {e}")
        sys.exit(1)


def print_transaction_record(record, title):
    """Print a full transaction record, including child details."""
    print(f"\n{title}")
    print(f"Transaction ID: {record.transaction_id}")
    print(f"Transaction Fee: {record.transaction_fee}")
    print(f"Transaction Hash: {record.transaction_hash.hex()}")
    print(f"Transaction Memo: {record.transaction_memo}")
    print(f"Receipt Status: {ResponseCode(record.receipt.status).name}")
    print(f"Receipt Account ID: {record.receipt.account_id}")
    print(f"Children: {record.children}")
    print(f"Duplicates Count: {len(record.duplicates)}")


def print_child_records(record):
    """Print all child transaction records in detail."""
    print(f"\nChild records count: {len(record.children)}")

    if not record.children:
        sys.exit(1)

    print_transaction_record(record.children[0], "Child record")


def main():
    try:
        client = Client.from_env()

        print("\nSTEP 1: Create a parent transaction with child records")
        transaction_id = submit_alias_auto_create_transfer(client)
        print(f"Parent transaction ID: {transaction_id}")

        print("\nSTEP 2: Querying parent transaction record with include_children=True...")
        record = TransactionRecordQuery().set_transaction_id(transaction_id).set_include_children(True).execute(client)

        print_transaction_record(record, "Parent Transaction Record")
        print_child_records(record)
    except Exception as e:
        print(f"Error running example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
