"""
uv run examples/transfer_nft.py
python examples/transfer_nft.py

"""
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
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    # Initialize network and client
    network = Network(os.getenv('NETWORK'))
    client = Client(network)

    # Set up operator account
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_test_account(client):
    """Create a new account for testing"""
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
        print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.account_id
    print(f"New account created with ID: {account_id}")
    
    return account_id, new_account_private_key

def create_nft(client, operator_id, operator_key):
    """Create a non-fungible token"""
    transaction = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_freeze_key(operator_key)
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    # Get token ID from receipt
    nft_token_id = receipt.token_id
    print(f"NFT created with ID: {nft_token_id}")
    
    return nft_token_id

def mint_nft(client, nft_token_id, operator_key):
    """Mint a non-fungible token"""
    transaction = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(b"My NFT Metadata 1")
        .freeze_with(client)
    )

    receipt = transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print(f"NFT minted with serial number: {receipt.serial_numbers[0]}")
    
    return NftId(nft_token_id, receipt.serial_numbers[0])

def associate_nft(client, account_id, token_id, account_private_key):
    """Associate a non-fungible token with an account"""
    # Associate the token_id with the new account
    associate_transaction = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_private_key) # Has to be signed by new account's key
    )
    
    receipt = associate_transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT association failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print("NFT successfully associated with account")

def transfer_nft_token(client, nft_id, sender_id, receiver_id):
    """Transfer the NFT from the sender to the receiver account"""
    # Transfer nft to the new account
    transfer_transaction = (
        TransferTransaction()
        .add_nft_transfer(nft_id, sender_id, receiver_id)
        .freeze_with(client)
    )
    
    receipt = transfer_transaction.execute(client)
    
    # Check if nft transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    print(f"Successfully transferred NFT to account {receiver_id}")

def main():
    """
    Demonstrates the nft transfer functionality by:
    1. Creating a new account
    2. Creating a nft
    3. Minting a nft
    4. Associating the nft with the new account
    5. Transferring the nft to the new account
    """
    client, operator_id, operator_key = setup_client()
    account_id, new_account_private_key = create_test_account(client)
    token_id = create_nft(client, operator_id, operator_key)
    nft_id = mint_nft(client, token_id, operator_key)
    associate_nft(client, account_id, token_id, new_account_private_key)
    
    # Transfer the NFT to the new account
    transfer_nft_token(client, nft_id, operator_id, account_id)


if __name__ == "__main__":
    main()