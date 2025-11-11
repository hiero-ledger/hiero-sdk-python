"""
uv run examples/tokens/token_unpause_transaction.py
python examples/tokens/token_unpause_transaction.py

"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    ResponseCode,
    TokenId,
    TokenType,
    TokenCreateTransaction,
    TokenUnpauseTransaction,
    TokenPauseTransaction,
    TokenInfoQuery
)

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""

    try:
        network = Network(network_name)
        print(f"Connecting to Hedera {network_name} network!")
        client = Client(network)
        
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

def create_token(client: Client, operator_id: AccountId, pause_key: PrivateKey,):
    """Create a fungible token"""
    print("\nCreating a token...")

    try:
        token_tx = (
            TokenCreateTransaction()
            .set_token_name("Token A")
            .set_token_symbol("TKA")
            .set_initial_supply(1)
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_pause_key(pause_key)         # Required for pausing tokens
            .freeze_with(client)
        )
    
        receipt = token_tx.sign(pause_key).execute(client)
    
        token_id = receipt.token_id
        print(f"✅ Success! Created token: {token_id}")
        check_pause_status(client, token_id)
    
        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

def pause_token(client: Client, token_id: TokenId, pause_key: PrivateKey):
    """Pause token"""
    print("\nAttempting to pause the token...")

    try:
        pause_tx = (
            TokenPauseTransaction()
            .set_token_id(token_id)
            .freeze_with(client)
            .sign(pause_key)
        )
    
        receipt = pause_tx.execute(client)

        if receipt.status == ResponseCode.SUCCESS:
            print(f"✅ Successfully paused token: {token_id}")
            check_pause_status(client, token_id)
        else:
            print(f"❌ Transaction completed, but status is: {receipt.status.name}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error pausing token: {e}")
        sys.exit(1)

def check_pause_status(client, token_id: TokenId):
    """Query and print the current paused/unpaused status of a token."""
    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Token status is now: {info.pause_status.name}")
    

def unpause_token():
    pause_key = PrivateKey.generate()
    client, operator_id, _ = setup_client()

    token_id = create_token(client, operator_id, pause_key)

    pause_token(client, token_id, pause_key)

    print("\nAttempting to Unpause the token...")

    unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )
    receipt = unpause_tx.execute(client)

    try:
        if receipt.status == ResponseCode.SUCCESS:
            print(f"✅ Successfully unpaused token: {token_id}")
            check_pause_status(client, token_id)
        else:
            print(f"❌ Transaction completed, but status is: {receipt.status.name}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error pausing token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    unpause_token()
