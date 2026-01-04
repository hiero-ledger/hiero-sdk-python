"""
Example: Approving an HBAR allowance and transferring HBAR using it.

Why:
    This example demonstrates how to approve and consume an HBAR allowance
    using the Hiero Python SDK when interacting with the Hedera network.

Key Concepts:
    - Owner: The account that owns the HBAR and grants the allowance.
    - Spender: The account authorized to spend HBAR on behalf of the Owner.
    - Receiver: The account that receives the transferred HBAR.
    - HBAR Allowance: Permission granted by the Owner allowing the Spender to
      transfer a specified amount of HBAR without taking custody of the funds.

High-Level Steps:
    Prerequisites:
        1. Initialize a client with an existing operator account as the Owner.

    Required:
        2. Create Spender and Receiver accounts.
        3. Approve an HBAR allowance from the Owner to the Spender.
        4. Submit a transfer transaction that consumes the allowance, moving
           HBAR from the Owner to the Receiver.

Notes:
    The transfer transaction is generated, signed, and paid for by the Spender,
    not the Owner. This reflects the delegated spending model described in the
    Hedera allowance documentation. This example focuses solely on HBAR
    allowances and does not demonstrate revoking allowances or token/NFT usage.
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
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> Client:
    """Initialize and set up the client with operator account using env vars."""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_account(client: Client):
    """Create a new Hedera account with initial balance."""
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
        print(
            "Account creation failed with status: "
            f"{ResponseCode(account_receipt.status).name}"
        )
        sys.exit(1)

    account_account_id = account_receipt.account_id

    return account_account_id, account_private_key


def approve_hbar_allowance(
    client: Client,
    owner_account_id: AccountId,
    spender_account_id: AccountId,
    amount: Hbar,
):
    """Approve Hbar allowance for spender."""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_hbar_allowance(owner_account_id, spender_account_id, amount)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            "Hbar allowance approval failed with status: "
            f"{ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Hbar allowance of {amount} approved for spender {spender_account_id}")
    return receipt


def transfer_hbar_with_allowance(
    client: Client,
    owner_account_id: AccountId,
    spender_account_id: AccountId,
    spender_private_key: PrivateKey,
    receiver_account_id: AccountId,
    amount: Hbar,
):
    """Transfer hbars using a previously approved allowance."""
    receipt = (
        TransferTransaction()
        # Transaction is paid for / initiated by spender
        .set_transaction_id(TransactionId.generate(spender_account_id))
        .add_approved_hbar_transfer(owner_account_id, -amount.to_tinybars())
        .add_approved_hbar_transfer(receiver_account_id, amount.to_tinybars())
        .freeze_with(client)
        .sign(spender_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Hbar transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(
        f"Successfully transferred {amount} from {owner_account_id} "
        f"to {receiver_account_id} using allowance"
    )

    return receipt


def main():
    """
    Demonstrates hbar allowance functionality by:
    1. Setting up client with operator account
    2. Creating spender and receiver accounts
    3. Approving hbar allowance for spender
    4. Transferring hbars using the allowance
    """
    client = setup_client()

    # Create spender and receiver accounts
    spender_id, spender_private_key = create_account(client)
    print(f"Spender account created with ID: {spender_id}")

    receiver_id, _ = create_account(client)
    print(f"Receiver account created with ID: {receiver_id}")

    # Approve hbar allowance for spender
    allowance_amount = Hbar(2)
    owner_account_id = client.operator_account_id

    approve_hbar_allowance(client, owner_account_id, spender_id, allowance_amount)

    # Transfer hbars using the allowance
    transfer_hbar_with_allowance(
        client=client,
        owner_account_id=owner_account_id,
        spender_account_id=spender_id,
        spender_private_key=spender_private_key,
        receiver_account_id=receiver_id,
        amount=allowance_amount,
    )


if __name__ == "__main__":
    main()
