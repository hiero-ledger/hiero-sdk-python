"""
Example demonstrating hbar allowance approval and usage.
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey, TransactionId
from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID",""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY",""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_account(client):
    """Create an account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    account_receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Account for hbar allowance")
        .execute(client)
    )

    if account_receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(account_receipt.status).name}")
        sys.exit(1)

    account_account_id = account_receipt.account_id

    return account_account_id, account_private_key


def approve_hbar_allowance(client, owner_account_id, spender_account_id, amount):
    """Approve Hbar allowance for spender"""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_hbar_allowance(owner_account_id, spender_account_id, amount)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Hbar allowance approval failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Hbar allowance of {amount} approved for spender {spender_account_id}")
    return receipt


def delete_hbar_allowance(client, owner_account_id, spender_account_id):
    """Delete hbar allowance by setting amount to 0"""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_hbar_allowance(owner_account_id, spender_account_id, Hbar(0))
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Hbar allowance deletion failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Hbar allowance deleted for spender {spender_account_id}")
    return receipt


def transfer_hbar_without_allowance(client, spender_account_id, spender_private_key, amount):
    """Transfer hbars without allowance"""
    print("Trying to transfer hbars without allowance...")
    owner_account_id = client.operator_account_id
    client.set_operator(spender_account_id, spender_private_key)  # Set operator to spender

    receipt = (
        TransferTransaction()
        .add_approved_hbar_transfer(owner_account_id, -amount.to_tinybars())
        .add_approved_hbar_transfer(spender_account_id, amount.to_tinybars())
        .execute(client)
    )

    if receipt.status != ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE:
        print(
            f"Hbar transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE "
            f"status but got: {ResponseCode(receipt.status).name}"
        )

    print(f"Hbar transfer successfully failed with {ResponseCode(receipt.status).name} status")


def hbar_allowance():
    """
    Demonstrates hbar allowance functionality by:
    1. Setting up client with operator account
    2. Creating spender and receiver accounts
    3. Approving hbar allowance for spender
    4. Transferring hbars using the allowance
    5. Deleting the allowance
    6. Attempting to transfer hbars without allowance (should fail)
    """
    client = setup_client()

    # Create spender and receiver accounts
    spender_id, spender_private_key = create_account(client)
    print(f"Spender account created with ID: {spender_id}")

    receiver_id, _ = create_account(client)
    print(f"Receiver account created with ID: {receiver_id}")

    # Approve hbar allowance for spender
    allowance_amount = Hbar(2)

    approve_hbar_allowance(client, client.operator_account_id, spender_id, allowance_amount)

    # Transfer hbars using the allowance
    receipt = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(spender_id))
        .add_approved_hbar_transfer(client.operator_account_id, -allowance_amount.to_tinybars())
        .add_approved_hbar_transfer(receiver_id, allowance_amount.to_tinybars())
        .freeze_with(client)
        .sign(spender_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Hbar transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Successfully transferred {allowance_amount} from", end=" ")
    print(f"{client.operator_account_id} to {receiver_id} using allowance")

    # Delete allowance
    delete_hbar_allowance(client, client.operator_account_id, spender_id)

    # Try to transfer hbars without allowance
    transfer_hbar_without_allowance(client, spender_id, spender_private_key, allowance_amount)


if __name__ == "__main__":
    hbar_allowance()
