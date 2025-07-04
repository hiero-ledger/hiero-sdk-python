import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    # Initialize network and client
    network = Network(network='testnet')
    client = Client(network)

    # Set up operator account
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_account_transaction(client):
    """Create a new account to get a transaction ID for record query"""
    # Generate a new key pair for the account
    new_account_key = PrivateKey.generate_ed25519()
    
    # Create the account
    receipt = (
        AccountCreateTransaction()
        .set_key(new_account_key.public_key())
        .set_initial_balance(Hbar(1))
        .execute(client)
    )
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    # Get the new account ID and transaction ID from receipt
    new_account_id = receipt.accountId
    transaction_id = receipt.transaction_id
    
    print(f"Account created with ID: {new_account_id}")
    
    return new_account_id, new_account_key, transaction_id

def create_fungible_token(client: 'Client', account_id, account_private_key):
    """Create a fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(100)
        .set_treasury_account_id(account_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_admin_key(account_private_key)
        .set_supply_key(account_private_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    token_id = receipt.tokenId
    print(f"\nFungible token created with ID: {token_id}")
    
    return token_id

def associate_token(client, token_id, receiver_id, receiver_private_key):
    """Associate token with an account"""
    # Associate the token_id with the new account
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(receiver_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(receiver_private_key) # Has to be signed here by receiver's key
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print(f"Token successfully associated with account: {receiver_id}")

def transfer_tokens(client, treasury_id, treasury_private_key, receiver_id, token_id, amount=10):
    """Transfer tokens to the receiver account so we can later reject them"""
    # Transfer tokens to the receiver account
    receipt = (
        TransferTransaction()
        .add_token_transfer(token_id, treasury_id, -amount)
        .add_token_transfer(token_id, receiver_id, amount)
        .freeze_with(client)
        .sign(treasury_private_key)
        .execute(client)
    )
    
    # Check if transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print(f"Successfully transferred {amount} tokens to receiver account {receiver_id}")
    
    return receipt

def print_transaction_record(record):
    """Print the transaction record"""
    print(f"Transaction ID: {record.transaction_id}")
    print(f"Transaction Fee: {record.transaction_fee}")
    print(f"Transaction Hash: {record.transaction_hash.hex()}")
    print(f"Transaction Memo: {record.transaction_memo}")
    print(f"Transaction Account ID: {record.receipt.accountId}")
    
    print(f"\nTransfers made in the transaction:")
    for account_id, amount in record.transfers.items():
        print(f"  Account: {account_id}, Amount: {amount}")

def query_record():
    """
    Demonstrates the transaction record query functionality by performing the following steps:
    1. Creating a new account transaction to get a transaction ID
    2. Querying and displaying the transaction record for account creation
    3. Creating a fungible token and associating it with the new account
    4. Transferring tokens from operator to new account
    5. Querying and displaying the transaction record for token transfer
    """
    client, operator_id, operator_key = setup_client()
    
    # Create a transaction to get a transaction ID
    new_account_id, new_account_key, transaction_id = create_account_transaction(client)
    
    record = (
        TransactionRecordQuery()
        .set_transaction_id(transaction_id)
        .execute(client)
    )
    print("Transaction record for account creation:")
    print_transaction_record(record)
    
    token_id = create_fungible_token(client, operator_id, operator_key)
    associate_token(client, token_id, new_account_id, new_account_key)
    transfer_receipt = transfer_tokens(client, operator_id, operator_key, new_account_id, token_id)
    
    transfer_record = (
        TransactionRecordQuery()
        .set_transaction_id(transfer_receipt.transaction_id)
        .execute(client)
    )
    print("Transaction record for token transfer:")
    print_transaction_record(transfer_record)
    
    print(f"\nToken Transfer Record:")
    for token_id, transfers in transfer_record.token_transfers.items():
        print(f"  Token ID: {token_id}")
        for account_id, amount in transfers.items():
            print(f"    Account: {account_id}, Amount: {amount}")

if __name__ == "__main__":
    query_record()
