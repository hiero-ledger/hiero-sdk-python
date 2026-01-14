"""
uv run examples/account/account_id_populate_from_mirror.py
python examples/account/account_id_populate_from_mirror.py

This example demonstrates how to populate AccountId fields
using mirror node lookups:

1. Create an AccountId from an EVM address
2. Trigger auto account creation via HBAR transfer
3. Populate account number (num) from mirror node
4. Populate EVM address from mirror node
"""

import sys
import time

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    Hbar,
    TransactionGetReceiptQuery
)

def generate_evm_address():
    """
    Generates a new ECDSA key pair and returns its EVM address.
    """
    private_key = PrivateKey.generate_ecdsa()
    return private_key.public_key().to_evm_address()


def auto_create_account(client, evm_address):
    """
    Triggers auto account creation by transferring HBAR
    to an EVM address.
    """
    print("\nAuto Account Creation...")

    try:
        evm_account_id = AccountId.from_evm_address(evm_address, 0, 0)

        transfer_tx = (
            TransferTransaction()
            .add_hbar_transfer(evm_account_id, Hbar(1).to_tinybars())
            .add_hbar_transfer(client.operator_account_id, Hbar(-1).to_tinybars())
            .execute(client)
        )

        receipt = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transfer_tx.transaction_id)
            .set_include_children(True)
            .execute(client)
        )
    except Exception as e:
        print(f"Failed during auto account creation tx: {e}")
        sys.exit(1)

    if not receipt.children:
        print("Auto account creation failed: no child receipts found")
        sys.exit(1)

    account_id = receipt.children[0].account_id
    print(f"Auto-created account: {account_id}")
    return account_id


def populate_account_num_example(client, evm_address, created_account_id):
    """
    Demonstrates populating AccountId.num from the mirror node.
    """
    print("\nExample 1: Populate Account Number from Mirror Node...")

    mirror_account_id = AccountId.from_evm_address(evm_address, 0, 0)
    print(f"Before populate: num = {mirror_account_id.num}")

    time.sleep(5)

    try:
        mirror_account_id.populate_account_num(client)
    except Exception as e:
        print(f"Failed to populate account number: {e}")
        sys.exit(1)

    print("After populate:")
    print(f"  Shard: {mirror_account_id.shard}")
    print(f"  Realm: {mirror_account_id.realm}")
    print(f"  Num:   {mirror_account_id.num}")

    if mirror_account_id.num != created_account_id.num:
        print(
            "Account number mismatch:\n"
            f"  Expected: {created_account_id.num}\n"
            f"  Got:      {mirror_account_id.num}"
        )
        sys.exit(1)


def populate_evm_address_example(client, created_account_id, evm_address):
    """
    Demonstrates populating AccountId.evm_address from the mirror node.
    """
    print("\nExample 2: Populate EVM Address from Mirror Node")

    print(f"Before populate: evm_address = {created_account_id.evm_address}")

    time.sleep(5)

    try:
        created_account_id.populate_evm_address(client)
    except Exception as e:
        print(f"Failed to populate EVM address: {e}")
        sys.exit(1)

    print(f"After populate: evm_address = {created_account_id.evm_address}")

    if created_account_id.evm_address != evm_address:
        print(
            "EVM address mismatch:\n"
            f"  Expected: {evm_address}\n"
            f"  Got:      {created_account_id.evm_address}"
        )
        sys.exit(1)


def main():
    client = Client.from_env()

    print(f"Client set up with operator id {client.operator_account_id}")

    evm_address = generate_evm_address()
    print(f"Generated EVM address: {evm_address}")

    created_account_id = auto_create_account(client, evm_address)

    populate_account_num_example(client, evm_address, created_account_id)
    populate_evm_address_example(client, created_account_id, evm_address)



if __name__ == "__main__":
    main()