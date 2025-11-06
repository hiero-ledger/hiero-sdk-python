"""
uv run examples/token_update_fungible.py
python examples/token_update_fungible.py

"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(os.getenv('NETWORK'))
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_fungible_token(client, operator_id, operator_key, metadata_key):
    """
    Create a fungible token
    
    If we want to update metadata later using TokenUpdateTransaction:
    1. Set a metadata_key and sign the update transaction with it, or
    2. Sign the update transaction with the admin_key
    
    Note: If no Admin Key was assigned during token creation (immutable token), 
    token updates will fail with TOKEN_IS_IMMUTABLE.
    """
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(100)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_freeze_key(operator_key)
        .set_metadata_key(metadata_key)
        .execute(client)
    )
    
    # Check if token creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get token ID from receipt
    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def get_token_info(client, token_id):
    """Get information about a fungible token"""
    info = (
        TokenInfoQuery()
        .set_token_id(token_id)
        .execute(client)
    )
    
    return info

def update_token_data(client, token_id, update_metadata, update_token_name, update_token_symbol, update_token_memo):
    """Update metadata for a fungible token"""
    receipt = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_metadata(update_metadata)
        .set_token_name(update_token_name)
        .set_token_symbol(update_token_symbol)
        .set_token_memo(update_token_memo)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token metadata update failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully updated token data")

def token_update_fungible():
    """
    Demonstrates the fungible token update functionality by:
    1. Setting up client with operator account
    2. Creating a fungible token with metadata key
    3. Checking the current token info
    4. Updating the token's metadata, name, symbol and memo
    5. Verifying the updated token info
    """
    client, operator_id, operator_key = setup_client()
    
    # Create metadata key
    metadata_private_key = PrivateKey.generate_ed25519()
    
    token_id = create_fungible_token(client, operator_id, operator_key, metadata_private_key)
    
    print("\nToken info before update:")
    token_info = get_token_info(client, token_id)
    print(token_info)
    
    # New data to update the fungible token
    update_metadata = b"Updated metadata"
    update_token_name = "Updated Token"
    update_token_symbol = "UPD"
    update_token_memo = "Updated memo"
    
    update_token_data(client, token_id, update_metadata, update_token_name, update_token_symbol, update_token_memo)
    
    print("\nToken info after update:")
    token_info = get_token_info(client, token_id)
    print(token_info)
    
if __name__ == "__main__":
    token_update_fungible()
