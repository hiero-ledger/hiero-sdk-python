import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.query.token_info_query import TokenInfoQuery

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

def assert_success(receipt, action: str):
    """
    Verify that a transaction or query succeeded, else raise.

    Args:
        receipt: The receipt object returned by `execute(client)` on a Transaction or Query.
        action (str): A short description of the attempted operation (e.g. "Token creation").

    Raises:
        RuntimeError: If the receipt’s status is not `ResponseCode.SUCCESS`, with a message
                      indicating which action failed and the status name.
    """
    if receipt.status != ResponseCode.SUCCESS:
        name = ResponseCode(receipt.status).name
        raise RuntimeError(f"{action!r} failed with status {name}")

def create_token(client, operator_id, admin_key, pause_key):
    """Create a fungible token"""
    # Create fungible token
    create_token_transaction = (
        TokenCreateTransaction()
        .set_token_name("Token123")
        .set_token_symbol("T123")
        .set_decimals(2)
        .set_initial_supply(10)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(admin_key)         # Required for token delete
        .set_pause_key(pause_key)         # Required for pausing tokens
        .freeze_with(client)
    )
    
    receipt = create_token_transaction.execute(client)
    assert_success(receipt, "Token creation")
    
    # Get token ID from receipt
    token_id = receipt.token_id
    print(f"Token created with ID: {token_id}")
    
    return token_id

def pause_token(client, token_id, pause_key):
    """Pause token"""
    # Note: This requires the pause key that was specified during token creation
    pause_transaction = (
        TokenPauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )
    
    receipt = pause_transaction.execute(client)
    assert_success(receipt, "Token pause")    

    print(f"Successfully paused token {token_id}")

def check_pause_status(client, token_id):
    """
    Query and print the current paused/unpaused status of a token.
    """
    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Token status is now: {info.pause_status.name}")
    
def delete_token(client, token_id, admin_key):
    """Delete token"""
    # Note: This requires the admin key that was specified during token creation
    delete_transaction = (
        TokenDeleteTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(admin_key)
    )

    receipt = delete_transaction.execute(client)
    assert_success(receipt, "Token delete")  

    print(f"Successfully deleted token {token_id}")

def token_pause():
    """
    Demonstrates the token pause functionality by:
      1. Creating a fungible token with pause and delete capability
      2. Pausing the token
      3. Verifying pause status
      4. Attempting (and failing) to delete the paused token because it is paused
    """
    client, operator_id, operator_key = setup_client()

    pause_key = operator_key  # for token pause 
    admin_key = operator_key  # for token delete 

    # Create token with required keys for pause and delete.
    token_id = create_token(client, operator_id, admin_key, pause_key)
    
    # Pause token using pause key – should succeed
    pause_token(client, token_id, pause_key)

    # Verify it is paused
    check_pause_status(client, token_id)

    # Try deleting token with admin key – should fail with TOKEN_IS_PAUSED
    try:
        delete_token(client, token_id, admin_key)
        print("❌ Whoops, delete succeeded—but it should have failed on a paused token!")
    except RuntimeError as e:
        print(f"✅ Unable to delete token as expected as it is paused: {e}")

if __name__ == "__main__":
    token_pause()
