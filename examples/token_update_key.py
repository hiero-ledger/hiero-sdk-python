
"""
uv run examples/token_update_key.py
python examples/token_update_key.py

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
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_key_validation import TokenKeyValidation
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
    
    return client, operator_id

def create_fungible_token(client, operator_id, admin_key, wipe_key):
    """Create a fungible token"""
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
        .set_admin_key(admin_key)
        .set_wipe_key(wipe_key)
        .freeze_with(client)
        .sign(admin_key)
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

def update_wipe_key_full_validation(client, token_id, old_wipe_key):
    """
    Update token wipe key with full validation mode.
    
    This demonstrates using FULL_VALIDATION mode (default) which requires both old and new key signatures.
    This ensures that there cannot be an accidental update to a public key for which the user does not possess
    the private key.
    Although only private keys can be set currently, the validation provides additional safety by requiring
    signatures from both keys.
    """
    # Generate new wipe key
    new_wipe_key = PrivateKey.generate_ed25519()
    
    receipt = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_wipe_key(new_wipe_key)
        .set_key_verification_mode(TokenKeyValidation.FULL_VALIDATION)
        .freeze_with(client)
        .sign(new_wipe_key)
        .sign(old_wipe_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token update failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Successfully updated wipe key")

    # Query token info to verify wipe key update
    info = get_token_info(client, token_id)
    print(f"Token's wipe key after update: {info.wipe_key}")

def token_update_key():
    """
    Demonstrates updating keys on a fungible token by:
    1. Setting up client with operator account
    2. Creating a fungible token with admin and wipe keys
    3. Checking the current token info and key values
    4. Updating the wipe key with full validation
    """
    client, operator_id = setup_client()
    
    admin_key = PrivateKey.generate_ed25519()
    wipe_key = PrivateKey.generate_ed25519()
    
    token_id = create_fungible_token(client, operator_id, admin_key, wipe_key)
    
    print("\nToken info before update:")
    token_info = get_token_info(client, token_id)
    
    print(f"Token's wipe key after creation: {token_info.wipe_key}")
    print(f"Token's admin key after creation: {token_info.admin_key}")
    
    update_wipe_key_full_validation(client, token_id, wipe_key)
    
if __name__ == "__main__":
    token_update_key()
