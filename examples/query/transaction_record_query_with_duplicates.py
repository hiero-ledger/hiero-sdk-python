"""
Demonstrates querying transaction records with duplicate submissions included.

Shows how to:
- Submit the same signed transaction multiple times
- Use TransactionRecordQuery with include_duplicates=True
- Access and display the duplicates list
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


def submit_duplicates(tx, client, count=2):
    """Submit the same transaction multiple times and handle expected duplicate responses."""
    for i in range(1, count + 1):
        print(f"Submitting duplicate #{i}...")
        try:
            receipt = tx.execute(client)
            status_name = ResponseCode(receipt.status).name
            print(f"  → receipt status: {status_name}")
        except PrecheckError as e:
            if e.status == ResponseCode.DUPLICATE_TRANSACTION:
                print("  → DUPLICATE_TRANSACTION in precheck (normal/expected)")
            else:
                print(f"  → Unexpected precheck failure: {e}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"  → Submission failed: {e}", file=sys.stderr)
            sys.exit(1)


def print_record_info(record):
    """Print main record and duplicates information."""
    main_status = ResponseCode(record.receipt.status).name
    memo = record.transaction_memo or '(none)'
    print(f"Main record   : status = {main_status:18}  memo = {memo}")

    print(f"Duplicates found: {len(record.duplicates)}")

    for i, dup in enumerate(record.duplicates, 1):
        dup_status = ResponseCode(dup.receipt.status).name
        memo = dup.transaction_memo or '(none)'
        print(f"  Duplicate #{i}: status = {dup_status:18}  memo = {memo}")


def _run():
    client = Client.from_env()  # reads OPERATOR_ID, OPERATOR_KEY, HEDERA_NETWORK from env

    new_key = PrivateKey.generate_ed25519()

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_key.public_key())
        .set_initial_balance(Hbar.from_tinybars(10_000_000))
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    print("Submitting original transaction...")
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"AccountCreate failed: {ResponseCode(receipt.status).name}", file=sys.stderr)
        sys.exit(1)

    tx_id = receipt.transaction_id
    print(f"Transaction ID: {tx_id}")

    # ────────────────────────────────────────────────
    # Submit duplicates — expect DUPLICATE_TRANSACTION
    # ────────────────────────────────────────────────
    submit_duplicates(tx, client, count=2)

    print("Waiting for consensus and mirror node propagation...")
    time.sleep(6)  # 3s is often too short on testnet/previewnet/local

    print("\nQuerying transaction record with include_duplicates=True...")
    record = (
        TransactionRecordQuery()
        .set_transaction_id(tx_id)
        .set_include_duplicates(True)
        .execute(client)
    )

    print_record_info(record)

    if not record.duplicates:
        print("\nTip: On some networks you may see 0 duplicates even after several submissions "
              "due to aggressive deduplication or mirror-node delay.")


if __name__ == "__main__":
    main()