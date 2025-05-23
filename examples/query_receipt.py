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
)

load_dotenv()

def query_receipt():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    recipient_id = AccountId.from_string(os.getenv('RECIPIENT_ID'))
    amount = 10

    client.set_operator(operator_id, operator_key)

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
    print(f"Transfer transaction status: {ResponseCode.get_name(receipt.status)}")

    receipt_query = TransactionGetReceiptQuery().set_transaction_id(transaction_id)
    queried_receipt = receipt_query.execute(client)
    print(f"Queried transaction status: {ResponseCode.get_name(queried_receipt.status)}")

if __name__ == "__main__":
    query_receipt()
