import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_update_nfts_transaction import TokenUpdateNftsTransaction
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_nft(client, operator_id, operator_key, metadata_key):
    """Create a non-fungible token"""
    receipt = (
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
        .set_freeze_key(operator_key)
        .set_supply_key(operator_key)
        .set_metadata_key(metadata_key)  # Needed to update NFTs
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
    
    return [NftId(nft_token_id, serial_number) for serial_number in receipt.serial_numbers], receipt.serial_numbers

def get_nft_info(client, nft_id):
    """Get information about an NFT"""
    info = (
        TokenNftInfoQuery()
        .set_nft_id(nft_id)
        .execute(client)
    )
    
    return info

def update_nft_metadata(client, nft_token_id, serial_numbers, new_metadata, metadata_private_key):
    """Update metadata for NFTs in a collection"""
    receipt = (
        TokenUpdateNftsTransaction()
        .set_token_id(nft_token_id)
        .set_serial_numbers(serial_numbers) 
        .set_metadata(new_metadata)
        .freeze_with(client)
        .sign(metadata_private_key)  # Has to be signed here by metadata_key
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT metadata update failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)

    print(f"Successfully updated metadata for NFTs with serial numbers: {serial_numbers}")

def token_update_nfts():
    """
    Demonstrates the NFT token update functionality by:
    1. Setting up client with operator account
    2. Creating a non-fungible token with metadata key
    3. Minting two NFTs with initial metadata
    4. Checking the current NFT info
    5. Updating metadata for the first NFT
    6. Verifying the updated NFT metadata
    """
    client, operator_id, operator_key = setup_client()
    
    # Create metadata key
    metadata_private_key = PrivateKey.generate_ed25519()
    
    # Create a new NFT collection with the treasury account as owner
    nft_token_id = create_nft(client, operator_id, operator_key, metadata_private_key)
    
    # Initial metadata for our NFTs
    initial_metadata = [b"Initial metadata 1", b"Initial metadata 2"]
    
    # New metadata to update the first NFT
    new_metadata = b"Updated metadata1"
    
    # Mint 2 NFTs in the collection with initial metadata
    nft_ids, serial_numbers = mint_nfts(client, nft_token_id, initial_metadata)
    
    # Get and print information about the NFTs
    print("\nCheck that the NFTs have the initial metadata")
    for nft_id in nft_ids:
        nft_info = get_nft_info(client, nft_id)
        print(f"NFT ID: {nft_info.nft_id}, Metadata: {nft_info.metadata}")
    
    # Update metadata for specific NFTs by providing their id and serial numbers
    # Only the NFTs with the provided serial numbers will have their metadata updated
    serial_numbers_to_update = [serial_numbers[0]]
    update_nft_metadata(client, nft_token_id, serial_numbers_to_update, new_metadata, metadata_private_key)
    
    # Get and print information about the NFTs
    print("\nCheck that only the first NFT has the updated metadata")
    for nft_id in nft_ids:
        nft_info = get_nft_info(client, nft_id)
        print(f"NFT ID: {nft_info.nft_id}, Metadata: {nft_info.metadata}")
    
if __name__ == "__main__":
    token_update_nfts()
