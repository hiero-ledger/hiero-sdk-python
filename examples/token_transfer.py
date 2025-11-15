"""
Example: Token Transfer Transaction (Modularized)

This example demonstrates transferring tokens (HBARs or custom tokens)
between two Hedera accounts using the Hiero Python SDK.
It has been refactored for modularity and clarity.

Functions:
- setup_client(): Initializes and configures the Hedera client.
- transfer_transaction(): Executes a token/HBAR transfer.
- account_balance_query(): Checks the account balance post-transfer.
- main(): Orchestrates the above functions.
"""

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    AccountBalanceQuery,
    Hbar,
)
import os


def setup_client() -> Client:
    """
    Set up the Hedera client for Testnet.

    Returns:
        Client: Configured Hedera client.
    """
    operator_id = AccountId.fromString(os.getenv("OPERATOR_ID", "0.0.1234"))
    operator_key = PrivateKey.fromString(os.getenv("OPERATOR_KEY", "302e..."))
    client = Client.for_testnet()
    client.set_operator(operator_id, operator_key)
    return client


def transfer_transaction(
    client: Client, sender: AccountId, receiver: AccountId, amount_tinybars: int
) -> str:
    """
    Perform an HBAR transfer transaction between two accounts.

    Args:
        client (Client): The active Hedera client.
        sender (AccountId): The sender account ID.
        receiver (AccountId): The receiver account ID.
        amount_tinybars (int): Amount to transfer in tinybars.

    Returns:
        str: The transaction ID.
    """
    print(f"🚀 Initiating transfer of {amount_tinybars} tinybars from {sender} to {receiver}...")
    txn = (
        TransferTransaction()
        .add_hbar_transfer(sender, Hbar.fromTinybars(-amount_tinybars))
        .add_hbar_transfer(receiver, Hbar.fromTinybars(amount_tinybars))
        .execute(client)
    )
    receipt = txn.get_receipt(client)
    print(f"✅ Transfer complete. Status: {receipt.status}")
    return str(txn.transaction_id)


def account_balance_query(client: Client, account_id: AccountId) -> None:
    """
    Query and print the account balance.

    Args:
        client (Client): The active Hedera client.
        account_id (AccountId): The account to query.
    """
    balance = AccountBalanceQuery().set_account_id(account_id).execute(client)
    print(f"💰 Balance for {account_id}: {balance.hbars.toTinybars()} tinybars")


def main() -> None:
    """
    Main entry point to perform token transfer and balance verification.
    """
    client = setup_client()

    sender = AccountId.fromString(os.getenv("SENDER_ID", "0.0.1234"))
    receiver = AccountId.fromString(os.getenv("RECEIVER_ID", "0.0.5678"))
    amount_tinybars = int(os.getenv("TRANSFER_AMOUNT", "1000"))

    txn_id = transfer_transaction(client, sender, receiver, amount_tinybars)

    print(f"🔍 Transaction ID: {txn_id}")
    print("\n📊 Checking updated balances:")
    account_balance_query(client, sender)
    account_balance_query(client, receiver)


if __name__ == "__main__":
    main()
