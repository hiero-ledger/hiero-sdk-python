import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
    TokenAssociateTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_wipe_transaction import TokenWipeTransaction

load_dotenv()

def token_wipe_transaction():
    """
    Demonstrates the token wipe functionality by:
    1. Creating a new account
    2. Creating a fungible token
    3. Associating the token with the new account
    4. Transferring tokens to the new account
    5. Wiping the tokens from the account
    """
    # Initialize network and client
    network = Network(network='testnet')
    client = Client(network)

    # Set up operator account
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)

    # Generate private key for new account
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()
    
    # Create new account with initial balance of 1 HBAR
    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(Hbar(1))
        .freeze_with(client)
    )
    receipt = transaction.execute(client)
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.accountId
    print(f"New account created with ID: {account_id}")
    
    # Create fungible token
    # Note: The wipe key is required to perform token wipe operations
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Token123")
        .set_token_symbol("T123")
        .set_decimals(2)
        .set_initial_supply(10)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(operator_key)      # For token management
        .set_supply_key(operator_key)     # For minting/burning
        .set_freeze_key(operator_key)     # For freezing accounts
        .set_wipe_key(operator_key)       # Required for wiping tokens
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    # Check if token creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get token ID from receipt
    token_id = receipt.tokenId
    print(f"Token created with ID: {token_id}")
    
    # Associate the token with the new account
    # Note: Accounts must be associated with tokens before they can receive them
    associate_transaction = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
    )
    # Has to be signed by new account's key
    associate_transaction.sign(new_account_private_key)
    
    receipt = associate_transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print("Token successfully associated with account")
    
    # Transfer tokens to the new account
    # Note: Negative amount for sender, positive for receiver
    amount = 10
    transfer_transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id, -amount)  # From operator
        .add_token_transfer(token_id, account_id, amount)    # To new account
        .freeze_with(client)
    )
    
    receipt = transfer_transaction.execute(client)
    
    # Check if token transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token transfer failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully transferred {amount} tokens to account {account_id}")

    # Wipe the tokens from the account
    # Note: This requires the wipe key that was specified during token creation
    transaction = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .set_amount(amount)
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token wipe failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully wiped {amount} tokens from account {account_id}")

if __name__ == "__main__":
    token_wipe_transaction()
