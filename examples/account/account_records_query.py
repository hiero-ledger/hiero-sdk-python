"""
Example demonstrating account records query on the network.
uv run examples/account/account_records_query.py
python examples/account/account_records_query.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
)
from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_account(client):
    """Create a test account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(2))
        .set_account_memo("Test account for records query")
        .freeze_with(client)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    account_id = receipt.account_id
    print(f"\nAccount created with ID: {account_id}")

    return account_id, account_private_key


def format_single_record(record, idx):
    """Format a single account record"""
    lines = []
    lines.append(f"\nRecord #{idx}")
    lines.append("-" * 80)

    transaction_id = getattr(record, "transaction_id", None)
    if transaction_id:
        lines.append(f"  Transaction ID: {transaction_id}")

    consensus_timestamp = getattr(record, "consensus_timestamp", None)
    if consensus_timestamp:
        lines.append(f"  Consensus Timestamp: {consensus_timestamp}")

    transaction_fee = getattr(record, "transaction_fee", None)
    if transaction_fee:
        lines.append(f"  Transaction Fee: {transaction_fee} tinybar")

    transaction_hash = getattr(record, "transaction_hash", None)
    if transaction_hash:
        lines.append(f"  Transaction Hash: {transaction_hash.hex()}")

    receipt = getattr(record, "receipt", None)
    if receipt:
        lines.append(f"  Receipt Status: {ResponseCode(receipt.status).name}")

    transfers = getattr(record, "transfers", None)
    if transfers:
        lines.append(f"  Transfers:")
        for account_id, amount_in_tinybar in transfers.items():
            amount_hbar = amount_in_tinybar / 100_000_000  # Convert tinybar to hbar
            lines.append(f"    {account_id}: {amount_hbar:+.8f} ℏ")

    lines.append("-" * 80)
    return "\n".join(lines)


def format_account_records(records):
    """Format account records for readable display"""
    if not records:
        return "No records found"

    output = ["=" * 80]

    for idx, record in enumerate(records, 1):
        output.append(format_single_record(record, idx))

    output.append("=" * 80)
    return "\n".join(output)


def query_account_records():
    """
    Demonstrates the account record query functionality by:
    1. Setting up client with operator account
    2. Creating a new account and setting it as the operator
    3. Querying account records and displaying basic information
    4. Performing a transfer transaction
    5. Querying account records again to see updated transaction history
    """
    client = setup_client()

    # Store the original operator account ID before creating new account
    original_operator_id = client.operator_account_id

    # Create a new account
    account_id, account_private_key = create_account(client)

    records_before = AccountRecordsQuery().set_account_id(account_id).execute(client)

    print(f"\nAccount {account_id} has {len(records_before)} transaction records")
    print("\nTransaction records (before transfer):")
    print(format_account_records(records_before))

    # Set the newly created account as the operator for executing the transfer
    client.set_operator(account_id, account_private_key)

    # Perform a transfer transaction from the newly created account to the original operator
    print(f"\nTransferring 1 ℏ from {account_id} to {original_operator_id}...")
    receipt = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(original_operator_id, Hbar(1).to_tinybars())
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    records_after = AccountRecordsQuery().set_account_id(account_id).execute(client)

    print(f"\nAccount {account_id} has {len(records_after)} transaction record(s)")
    print("\nTransaction records (after transfer):")
    print(format_account_records(records_after))


if __name__ == "__main__":
    query_account_records()
