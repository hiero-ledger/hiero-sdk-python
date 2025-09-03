import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    Hbar,
    TransactionGetReceiptQuery,
    ResponseCode,
    AccountCreateTransaction
)

load_dotenv()

def query_receipt():
    """
    A full example that include account creation, Hbar transfer, and receipt querying
    """
    # Config Client
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

    # Create a new recipient account.
    print("\nCreating a new recipient account...")
    recipient_key = PrivateKey.generate()
    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)

    # Transfer Hbar to recipient account
    print("\nTransferring Hbar...")
    amount = 10
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -Hbar(amount).to_tinybars())
        .add_hbar_transfer(recipient_id, Hbar(amount).to_tinybars())
        .freeze_with(client)
        .sign(operator_key)
    )

    receipt = transaction.execute(client)
    transaction_id = transaction.transaction_id
    print(f"Transaction ID: {transaction_id}")
    print(f"✅ Success! Transfer transaction status: {ResponseCode(receipt.status).name}")

    # Query Transaction Receipt
    print("\nQuerying transaction receipt...")
    receipt_query = TransactionGetReceiptQuery().set_transaction_id(transaction_id)
    queried_receipt = receipt_query.execute(client)
    print(f"✅ Success! Queried transaction status: {ResponseCode(queried_receipt.status).name}")

if __name__ == "__main__":
    query_receipt()
