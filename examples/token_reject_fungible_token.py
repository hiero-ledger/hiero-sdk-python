import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client

def create_test_account(client):
    """Create a new account for testing"""
    # Generate private key for new account
    new_account_private_key = PrivateKey.generate_ed25519()
    new_account_public_key = new_account_private_key.public_key()
    
    # Create new account with initial balance of 1 HBAR
    receipt = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(Hbar(1))
        .execute(client)
    )
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.accountId
    print(f"New account created with ID: {account_id}")
    
    return account_id, new_account_private_key

def create_fungible_token(client: 'Client', treasury_id, treasury_private_key):
    """Create a fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(100)
        .set_treasury_account_id(treasury_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_admin_key(treasury_private_key)
        .set_supply_key(treasury_private_key)
        .set_freeze_key(treasury_private_key)
        .freeze_with(client)
        .sign(treasury_private_key) # Has to be signed by treasury account's key as we set the treasury_account_id to be the treasury_id
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    token_id = receipt.tokenId
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def associate_token(client, receiver_id, token_id, receiver_private_key):
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
    
def get_token_balances(client, treasury_id, receiver_id, token_id):
    """Get token balances for both accounts"""
    token_balance = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(treasury_id)
        .execute(client)
    )
    print(f"Token balance of treasury {treasury_id}: {token_balance.token_balances[token_id]}")
    
    receiver_token_balance = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(receiver_id)
        .execute(client)
    )
    print(f"Token balance of receiver {receiver_id}: {receiver_token_balance.token_balances[token_id]}")

def token_reject_fungible():
    """
    Demonstrates the fungible token reject functionality by:
    1. Creating a new treasury account
    2. Creating a new receiver account
    3. Creating a fungible token with the treasury account as owner
    4. Associating the token with the receiver account
    5. Transferring tokens to the receiver account
    6. Rejecting the tokens from the receiver account
    """
    client = setup_client()
    # Create treasury/sender account that will create and send tokens
    treasury_id, treasury_private_key = create_test_account(client)
    # Create receiver account that will receive and later reject tokens
    receiver_id, receiver_private_key = create_test_account(client)
    
    # Create a fungible token with the treasury account as owner and signer
    token_id = create_fungible_token(client, treasury_id, treasury_private_key)
    
    # Associate token with the receiver account so they can receive the tokens from the treasury
    associate_token(client, receiver_id, token_id, receiver_private_key)
    
    # Transfer tokens to the receiver account
    transfer_tokens(client, treasury_id, treasury_private_key, receiver_id, token_id)

    # Get and print token balances before rejection to show the initial state
    print("\nToken balances before rejection:")
    get_token_balances(client, treasury_id, receiver_id, token_id)
    
    # Receiver rejects the fungible tokens that were previously transferred to them
    receipt = (
        TokenRejectTransaction()
        .set_owner_id(receiver_id)
        .set_token_ids([token_id])
        .freeze_with(client)
        .sign(receiver_private_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token rejection failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
        
    print(f"Successfully rejected token {token_id} from account {receiver_id}")
    
    # Get and print token balances after rejection to show the final state
    print("\nToken balances after rejection:")
    get_token_balances(client, treasury_id, receiver_id, token_id)
    
if __name__ == "__main__":
    token_reject_fungible()
