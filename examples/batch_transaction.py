import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction



load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()
operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client

def batch_transaction():
    client = setup_client()
    batch_key = PrivateKey.generate()

    # tx1 = (
    #     TransferTransaction()
    #     .add_hbar_transfer(operator_id, -1)
    #     .add_hbar_transfer(AccountId.from_string("0.0.4951978"), 1)
    #     .set_batch_key(batch_key)  
    #     .freeze_with(client)
    #     .sign(operator_key)
    # )

    tx2 = (
        AccountCreateTransaction()
        .set_key(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .set_batch_key(batch_key)
        .freeze_with(client)
        .sign(operator_key)
    )

    tx = (
        BatchTransaction()
        .add_inner_transaction(tx2)
        .freeze_with(client)
        .sign(batch_key)
    )

    # print(tx1.node_account_id)

    print(tx.execute(client))
    print(tx.get_inner_transactions_ids()[0].account_id)

batch_transaction()