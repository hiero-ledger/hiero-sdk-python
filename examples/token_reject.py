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
from hiero_sdk_python.account.account_balance import AccountBalance
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction

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
        .set_initial_balance(Hbar(2))
        .execute(client)
    )
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.accountId
    print(f"New account created with ID: {account_id}")
    
    return account_id, new_account_private_key

def create_nft(client, account_id, new_account_private_key):
    """Create a non-fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(account_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(client.operator_private_key)
        .set_supply_key(client.operator_private_key)
        .set_freeze_key(client.operator_private_key)
        .freeze_with(client)
        .sign(new_account_private_key)
        .execute(client)
    )
    
    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get token ID from receipt
    nft_token_id = receipt.tokenId
    print(f"NFT created with ID: {nft_token_id}")
    
    return nft_token_id

def mint_nfts(client, nft_token_id, metadata_list):
    """Mint a non-fungible token"""
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(metadata_list)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"NFT minted with serial numbers: {receipt.serial_numbers}")
    
    return [NftId(nft_token_id, serial_number) for serial_number in receipt.serial_numbers]

def associate_tokens(client, account_id, nft_token_id, token_id, account_private_key):
    """Associate tokens with an account"""
    # Associate the token_ids with the new account
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(nft_token_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_private_key) # Has to be signed by new account's key
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Tokens successfully associated with account: {account_id}")

def create_fungible_token(client, account_id, new_account_private_key):
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
        .set_admin_key(client.operator_private_key)
        .set_supply_key(client.operator_private_key)
        .freeze_with(client)
        .sign(new_account_private_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    token_id = receipt.tokenId
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def transfer_tokens(client, account_id, new_account_private_key, receiver_id, token_id, nft_ids):
    """Transfer tokens to the new account"""
    # Transfer tokens to the new account
    receipt = (
        TransferTransaction()
        .add_nft_transfer(nft_ids[0], account_id, receiver_id)
        .add_nft_transfer(nft_ids[1], account_id, receiver_id)
        .add_token_transfer(token_id, account_id, -10)
        .add_token_transfer(token_id, receiver_id, 10)
        .freeze_with(client)
        .sign(new_account_private_key)
        .execute(client)
    )
    
    # Check if transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully transferred tokens to account {account_id}")
    
def get_token_balances(client, account_id, receiver_id, token_id, nft_token_id):
    """Get token balances for both accounts"""
    token_balance = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(account_id)
        .execute(client)
    )
    print(f"Token balance of account {account_id}: {token_balance.token_balances[token_id]}")
    print(f"NFT balance of account {account_id}: {token_balance.token_balances[nft_token_id]}")
    
    receiver_token_balance = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(receiver_id)
        .execute(client)
    )
    print(f"Token balance of receiver {receiver_id}: {receiver_token_balance.token_balances[token_id]}")
    print(f"NFT balance of receiver {receiver_id}: {receiver_token_balance.token_balances[nft_token_id]}")

def token_reject():
    """
    Demonstrates the token reject functionality by:
    1. Creating a new account
    2. Creating a non-fungible token
    3. Minting two NFTs
    4. Creating a fungible token
    5. Associating the NFTs and fungible token with the new account
    6. Transferring the tokens to the new account
    7. Rejecting the fungible token
    8. Rejecting the NFTs
    """
    client = setup_client()
    # Create test accounts
    account_id, new_account_private_key = create_test_account(client)
    receiver_id, receiver_private_key = create_test_account(client)
    
    # Create NFTs
    nft_token_id = create_nft(client, account_id, new_account_private_key)
    nft_ids = mint_nfts(client, nft_token_id, [b"ExampleMetadata 1", b"ExampleMetadata 2"])
    
    # Create fungible token
    token_id = create_fungible_token(client, account_id, new_account_private_key)
    
    # Associate tokens with the receiver account
    associate_tokens(client, receiver_id, nft_token_id, token_id, receiver_private_key)
    
    # Transfer tokens to the receiver account
    transfer_tokens(client, account_id, new_account_private_key, receiver_id, token_id, nft_ids)

    # Get token balances
    get_token_balances(client, account_id, receiver_id, token_id, nft_token_id)
    
    # Reject the fungible tokens
    receipt = (
        TokenRejectTransaction()
        .set_owner_id(receiver_id)
        .set_token_ids([token_id])
        .freeze_with(client)
        .sign(receiver_private_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token rejection failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
        
    print(f"Successfully rejected token {token_id} from account {receiver_id}")
    
    # Reject the NFTs
    receipt = (
        TokenRejectTransaction()
        .set_owner_id(receiver_id)
        .set_nft_ids([nft_ids[0], nft_ids[1]])
        .freeze_with(client)
        .sign(receiver_private_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT rejection failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully rejected NFTs {nft_ids[0]} and {nft_ids[1]} from account {receiver_id}")
    
    # Get token balances
    get_token_balances(client, account_id, receiver_id, token_id, nft_token_id)
    
if __name__ == "__main__":
    token_reject()
