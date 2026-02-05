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

def main():
    client = Client.from_env()  # reads OPERATOR_ID, OPERATOR_KEY, HEDERA_NETWORK from env
    if not client.operator_account_id or not client.operator_key:
        print("Error: OPERATOR_ID and OPERATOR_KEY environment variables must be set.")
        return
    
    new_key = PrivateKey.generate_ed25519()

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_key.public_key())
        .set_initial_balance(Hbar.from_tinybars(10_000_000))
        .freeze_with(client)
        .sign(client.operator_key)
    )

    print("Submitting original transaction...")
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"AccountCreate failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    tx_id = receipt.transaction_id
    print(f"TxID: {tx_id}")

    print("Submitting duplicate #1...")
    dup1_receipt = tx.execute(client)
    if dup1_receipt.status not in (
        ResponseCode.DUPLICATE_TRANSACTION,
        ResponseCode.SUCCESS,
    ):
        print(
            f"Duplicate `#1` unexpected status: {ResponseCode(dup1_receipt.status).name}"
        )
        sys.exit(1)

    print("Submitting duplicate #2...")
    dup2_receipt = tx.execute(client)
    if dup2_receipt.status not in (
        ResponseCode.DUPLICATE_TRANSACTION,
        ResponseCode.SUCCESS,
    ):
        print(
            f"Duplicate `#2` unexpected status: {ResponseCode(dup2_receipt.status).name}"
        )
        sys.exit(1)

    time.sleep(3)  # give consensus time (increase if needed)

    print("\nQuerying with include_duplicates=True...")
    record = (
        TransactionRecordQuery()
        .set_transaction_id(tx_id)
        .set_include_duplicates(True)
        .execute(client)
    )

    print(f"Main record: memo={record.transaction_memo or '(none)'}, "
          f"status={record.receipt.status.name}")

    print(f"Duplicates found: {len(record.duplicates)}")

    for i, dup in enumerate(record.duplicates, 1):
        print(f"  Duplicate #{i}: "
              f"status={dup.receipt.status.name}, "
              f"memo={dup.transaction_memo or '(none)'}")

if __name__ == "__main__":
    main()
