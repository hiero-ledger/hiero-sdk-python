"""
Example demonstrating fungible token allowance approval and usage.
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
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(os.getenv('NETWORK'))
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_account(client):
    """Create an account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    account_receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Account for token allowance")
        .execute(client)
    )

    if account_receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(account_receipt.status).name}")
        sys.exit(1)

    account_account_id = account_receipt.account_id

    return account_account_id, account_private_key


def create_fungible_token(client):
    """Create a fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("Test Token")
        .set_token_symbol("TT")
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(client.operator_account_id)
        .set_admin_key(client.operator_private_key)
        .set_supply_key(client.operator_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    return token_id


def associate_token_with_account(client, account_id, account_private_key, token_id):
    """Associate token with account"""
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Token {token_id} associated with account {account_id}")


def approve_token_allowance(client, token_id, owner_account_id, spender_account_id, amount):
    """Approve token allowance for spender"""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_allowance(token_id, owner_account_id, spender_account_id, amount)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token allowance approval failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Token allowance of {amount} approved for spender {spender_account_id}")
    return receipt


def delete_token_allowance(client, token_id, owner_account_id, spender_account_id):
    """Delete token allowance by setting amount to 0"""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_allowance(token_id, owner_account_id, spender_account_id, 0)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token allowance deletion failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Token allowance deleted for spender {spender_account_id}")
    return receipt


def transfer_token_without_allowance(
    client, spender_account_id, spender_private_key, amount, receiver_account_id, token_id
):
    """Transfer tokens without allowance"""
    print("Trying to transfer tokens without allowance...")
    owner_account_id = client.operator_account_id
    client.set_operator(spender_account_id, spender_private_key)  # Set operator to spender

    receipt = (
        TransferTransaction()
        .add_approved_token_transfer(token_id, owner_account_id, -amount)
        .add_approved_token_transfer(token_id, receiver_account_id, amount)
        .execute(client)
    )

    if receipt.status != ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE:
        print(
            f"Token transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE "
            f"status but got: {ResponseCode(receipt.status).name}"
        )

    print(f"Token transfer successfully failed with {ResponseCode(receipt.status).name} status")


def token_allowance():
    """
    Demonstrates fungible token allowance functionality by:
    1. Setting up client with operator account
    2. Creating spender and receiver accounts
    3. Creating a fungible token and associating it with the receiver account
    4. Approving token allowance for spender
    5. Transferring tokens using the allowance
    6. Deleting the allowance
    7. Attempting to transfer tokens without allowance (should fail)
    """
    client = setup_client()

    # Create spender and receiver accounts
    spender_id, spender_private_key = create_account(client)
    print(f"Spender account created with ID: {spender_id}")

    receiver_id, receiver_private_key = create_account(client)
    print(f"Receiver account created with ID: {receiver_id}")

    # Create fungible token
    token_id = create_fungible_token(client)

    # Associate token with receiver account
    associate_token_with_account(client, receiver_id, receiver_private_key, token_id)

    # Approve token allowance for spender
    allowance_amount = 20

    approve_token_allowance(
        client, token_id, client.operator_account_id, spender_id, allowance_amount
    )

    # Transfer tokens using the allowance
    receipt = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(spender_id))
        .add_approved_token_transfer(token_id, client.operator_account_id, -allowance_amount)
        .add_approved_token_transfer(token_id, receiver_id, allowance_amount)
        .freeze_with(client)
        .sign(spender_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Successfully transferred {allowance_amount} from", end=" ")
    print(f"{client.operator_account_id} to {receiver_id} using allowance")

    # Delete allowance
    delete_token_allowance(client, token_id, client.operator_account_id, spender_id)

    # Try to transfer tokens without allowance
    transfer_token_without_allowance(
        client, spender_id, spender_private_key, allowance_amount, receiver_id, token_id
    )


if __name__ == "__main__":
    token_allowance()
