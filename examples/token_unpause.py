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
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_info_query import TokenInfoQuery

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)

    return client, operator_id, operator_key

def assert_success(receipt, action: str):
    if receipt.status != ResponseCode.SUCCESS:
        name = ResponseCode.get_name(receipt.status)
        raise RuntimeError(f"{action!r} failed with status {name}")

def create_token(client, operator_id, admin_key, pause_key):
    """Create a fungible token with pause capability"""
    create_token_transaction = (
        TokenCreateTransaction()
        .set_token_name("DemoToken")
        .set_token_symbol("DT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_admin_key(admin_key)
        .set_pause_key(pause_key)
        .freeze_with(client)
    )

    receipt = create_token_transaction.execute(client)
    assert_success(receipt, "Token creation")
    return receipt.tokenId

def pause_token(client, token_id, pause_key):
    """Pause the token"""
    pause_transaction = (
        TokenPauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )
    receipt = pause_transaction.execute(client)
    assert_success(receipt, "Token pause")

def unpause_token(client, token_id, pause_key):
    """Unpause the token"""
    unpause_transaction = (
        TokenUnpauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )
    receipt = unpause_transaction.execute(client)
    assert_success(receipt, "Token unpause")

def check_token_status(client, token_id):
    """Check and print token status"""
    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Token status: {info.token_status.name}")

def delete_token(client, token_id, admin_key):
    """Delete the token"""
    delete_transaction = (
        TokenDeleteTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(admin_key)
    )
    receipt = delete_transaction.execute(client)
    assert_success(receipt, "Token delete")

def token_unpause_demo():
    """
    Demonstrates token unpause functionality:
    1. Creates token with pause capability
    2. Pauses the token
    3. Verifies paused status
    4. Unpauses the token
    5. Verifies unpaused status
    6. Deletes the token
    """
    client, operator_id, operator_key = setup_client()
    pause_key = operator_key
    admin_key = operator_key

    try:
        # 1. Create token
        token_id = create_token(client, operator_id, admin_key, pause_key)
        print(f"Created token {token_id}")

        # 2. Pause token
        pause_token(client, token_id, pause_key)
        check_token_status(client, token_id)

        # 3. Unpause token
        unpause_token(client, token_id, pause_key)
        check_token_status(client, token_id)

        # 4. Delete token (should succeed now that it's unpaused)
        delete_token(client, token_id, admin_key)
        print(f"Successfully deleted token {token_id}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    token_unpause_demo()
    