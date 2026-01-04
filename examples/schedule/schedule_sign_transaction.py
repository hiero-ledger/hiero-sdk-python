"""
Example demonstrating Schedule Sign functionality.

Execution rule:
- The network executes the scheduled transaction once it has collected
  all required signatures for the *inner* transaction.
- The payer/scheduler signature is only for creating the Schedule itself.
  It does NOT count toward the inner transaction’s required signers unless
  that same key is also required by the inner transaction.
- The admin key (if set) is only for delete/modify and is NOT required for execution.

In this example we schedule a transfer FROM a newly created account TO the operator.
Therefore, the only required signature for execution is the sender’s (new account) key.

uv run examples/schedule/schedule_sign_transaction.py
python examples/schedule/schedule_sign_transaction.py
"""

import datetime
import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.schedule.schedule_sign_transaction import ScheduleSignTransaction
from hiero_sdk_python.timestamp import Timestamp
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
        .set_account_memo("Test account for schedule sign")
        .freeze_with(client)
        .sign(account_private_key)
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


def create_schedule(client, account_id):
    """Create a scheduled transaction"""
    # Amount to transfer in tinybars
    amount = Hbar(1).to_tinybars()

    # Create a transfer transaction
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -amount)
        .add_hbar_transfer(client.operator_account_id, amount)
    )

    # Convert the transfer transaction into a scheduled transaction
    schedule_tx = transfer_tx.schedule()

    # Set expiration time for the scheduled transaction (90 seconds from now)
    expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=90)

    receipt = (
        schedule_tx.set_payer_account_id(
            client.operator_account_id
        )  # payer of the transaction fee
        .set_admin_key(
            client.operator_private_key.public_key()
        )  # delete/modify the transaction
        .set_expiration_time(Timestamp.from_date(expiration_time))
        .set_wait_for_expiry(False)  # don't wait for expiry, execute when signed
        .set_schedule_memo("Test schedule for signing")
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Schedule creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Schedule created with ID: {receipt.schedule_id}")

    return receipt.schedule_id


def _fmt_ts(ts):
    """Return a human-friendly timestamp string (defensive)."""
    if ts is None:
        return "None"
    try:
        # If it's an SDK Timestamp
        return ts.to_datetime().isoformat(sep=" ", timespec="seconds")
    except AttributeError:
        # If it's already a datetime or something else printable
        try:
            return ts.isoformat(sep=" ", timespec="seconds")
        except Exception:
            return str(ts)


def query_schedule_info(client, schedule_id, required_inner_keys=None):
    """Query and display schedule information (including missing signatures if known)"""
    info = ScheduleInfoQuery().set_schedule_id(schedule_id).execute(client)

    print("\nSchedule Info:")
    print(f"Schedule ID: {info.schedule_id}")
    print(f"Creator Account ID: {info.creator_account_id}")
    print(f"Payer Account ID: {info.payer_account_id}")
    print(f"Executed At: {_fmt_ts(info.executed_at)}")
    print(f"Expiration Time: {_fmt_ts(info.expiration_time)}")
    print(f"Schedule Memo: {info.schedule_memo}")
    print(f"Admin Key: {info.admin_key}")
    print(f"Wait For Expiry: {info.wait_for_expiry}")
    print(f"Collected Signers: {len(info.signers)}")
    for i, signer in enumerate(info.signers):
        print(f"  Signer {i+1}: {signer}")

    # Show which signatures are still missing for the inner txn, if provided
    if required_inner_keys:
        collected_str = {str(s) for s in info.signers}
        required_str = {str(k) for k in required_inner_keys}
        missing = list(required_str - collected_str)
        if missing:
            print(f"Missing required signatures: {len(missing)}")
            for m in missing:
                print(f"  Missing: {m}")
        else:
            print("All required inner-txn signatures have been collected.")


def schedule_sign():
    """
    Demonstrates schedule sign functionality by:
    1. Setting up client with operator account
    2. Creating a test account
    3. Creating a scheduled transfer transaction
    4. Querying the schedule info before signing
    5. Signing the scheduled transaction to execute it
    6. Querying the schedule info after signing to verify execution
    """
    client = setup_client()

    # Create an account first
    account_id, account_private_key = create_account(client)
    account_public_key = account_private_key.public_key()

    # Create a schedule
    schedule_id = create_schedule(client, account_id)

    # Query schedule info before signing
    print("\nSchedule Info Before Signing:")
    # Only the sender (new account) is required for execution in this example
    required_inner_keys = [account_public_key]
    query_schedule_info(client, schedule_id, required_inner_keys)

    # Sign the scheduled transaction to execute it
    print("\nSigning Schedule...")
    receipt = (
        ScheduleSignTransaction()
        .set_schedule_id(schedule_id)
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Schedule sign failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Schedule signed successfully!")

    # Query schedule info after signing to verify execution
    print("\nSchedule Info After Signing:")
    query_schedule_info(client, schedule_id, required_inner_keys)


if __name__ == "__main__":
    schedule_sign()
