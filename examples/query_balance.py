import os
import sys
import time
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    TransferTransaction,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
)

load_dotenv()

def create_account_and_transfer():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)

    # Create new account
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()
    transaction = AccountCreateTransaction(
        key=new_account_public_key,
        initial_balance=Hbar(10),  # 10 HBAR
        memo="New Account"
    ).freeze_with(client)
    transaction.sign(operator_key)
    receipt = transaction.execute(client)
    new_account_id = receipt.account_id

    # Check balance
    balance_query = CryptoGetAccountBalanceQuery().set_account_id(new_account_id)
    balance = balance_query.execute(client)
    print(f"Initial balance of new account: {balance.hbars} hbars")

    # Transfer 5 HBAR from operator to new account
    transfer_amount = Hbar(5)
    transfer_transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -transfer_amount.to_tinybars())
        .add_hbar_transfer(new_account_id, transfer_amount.to_tinybars())
        .freeze_with(client)
    )
    transfer_transaction.sign(operator_key)
    transfer_receipt = transfer_transaction.execute(client)
    print(f"Transfer transaction status: {ResponseCode(transfer_receipt.status).name}")

    time.sleep(2)

    # Check updated balance
    updated_balance_query = CryptoGetAccountBalanceQuery().set_account_id(new_account_id)
    updated_balance = updated_balance_query.execute(client)
    print(f"Updated balance of new account: {updated_balance.hbars} hbars")

if __name__ == "__main__":
    create_account_and_transfer()
