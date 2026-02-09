"""
Demonstrates behavior when submitting duplicate transactions and querying records.

Key points shown:
- Submitting the same signed transaction multiple times usually fails with DUPLICATE_TRANSACTION (precheck)
- No duplicate records are created for precheck-rejected submissions
- TransactionRecordQuery with include_duplicates=True returns an empty duplicates list in normal cases
- This is the expected behavior on mainnet/testnet — real duplicate records are rare
  (only occur with near-simultaneous consensus from multiple nodes)

Do NOT expect to see non-empty duplicates in this example — that's intentional.
"""

import sys
import time
from hiero_sdk_python import Client
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.exceptions import PrecheckError


def main():
    try:
        _run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def submit_duplicates(tx, client, count=3):
    """Submit the same signed transaction multiple times — expect duplicates to fail precheck."""
    for i in range(1, count + 1):
        print(f"\nSubmitting attempt #{i} (same transaction bytes)...")
        try:
            receipt = tx.execute(client)
            status_name = ResponseCode(receipt.status).name
            print(f"  → Unexpected success: {status_name}")
            print("     (This is rare — means the duplicate reached consensus before rejection)")
        except PrecheckError as e:
            if e.status == ResponseCode.DUPLICATE_TRANSACTION:
                print("  → DUPLICATE_TRANSACTION (expected — precheck rejection)")
            else:
                print(f"  → Unexpected precheck error: {e.status.name}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"  → Other failure: {e}", file=sys.stderr)
            sys.exit(1)


def print_record_info(record):
    """Print summary of the main record and any duplicates (usually none)."""
    main_status = ResponseCode(record.receipt.status).name
    memo = record.transaction_memo or '(none)'

    print("\nMain record:")
    print(f"  Status     : {main_status}")
    print(f"  Memo       : {memo}")
    print(f"  Duplicates : {len(record.duplicates)}")

    if record.duplicates:
        print("\nDuplicates (rare in normal operation):")
        for i, dup in enumerate(record.duplicates, 1):
            dup_status = ResponseCode(dup.receipt.status).name
            dup_memo = dup.transaction_memo or '(none)'
            print(f"  #{i:2} | Status: {dup_status:18} | Memo: {dup_memo}")
    else:
        print("  (No duplicate records — this is normal when duplicates are rejected at precheck)")


def _run():
    client = Client.from_env()  # Expects OPERATOR_ID, OPERATOR_KEY, HEDERA_NETWORK in env

    print("Creating a test transaction (AccountCreate)...")
    new_key = PrivateKey.generate_ed25519()

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_key.public_key())
        .set_initial_balance(Hbar.from_tinybars(10_000_000))
        .set_transaction_memo("Duplicate demo — original")
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    print("Submitting original transaction...")
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Original transaction failed: {ResponseCode(receipt.status).name}", file=sys.stderr)
        sys.exit(1)

    tx_id = receipt.transaction_id
    print(f"Original Transaction ID: {tx_id}")

    # Submit duplicates — almost always rejected at precheck
    submit_duplicates(tx, client, count=3)

    print("\nWaiting briefly for record availability (mirror node propagation)...")
    time.sleep(5)  # Usually enough on testnet; increase if needed

    print("\nQuerying record with include_duplicates=True...")
    record = (
        TransactionRecordQuery()
        .set_transaction_id(tx_id)
        .set_include_duplicates(True)
        .execute(client)
    )

    print_record_info(record)

    print("\nConclusion:")
    print("• Duplicate submissions were rejected with DUPLICATE_TRANSACTION (precheck)")
    print("• No duplicate records were stored → duplicates list is empty")
    print("• This is the typical / expected outcome")
    print("• Real duplicate records only appear in rare race conditions (near-simultaneous consensus)")


if __name__ == "__main__":
    main()
