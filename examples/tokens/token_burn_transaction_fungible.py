"""
uv run examples/token_burn_transaction_fungible.py 
python examples/token_burn_transaction_fungible.py

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
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction

load_dotenv()

network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
    print(f"Client set up with operator id {client.operator_account_id}")

    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_fungible_token(client, operator_id, operator_key):
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
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def get_token_info(client, token_id):
    """Get token info for the token"""
    token_info = (
        TokenInfoQuery()
        .set_token_id(token_id)
        .execute(client)
    )
    
    print(f"Token supply: {token_info.total_supply}")

def token_burn_fungible():
    """
    Demonstrates the fungible token burn functionality by:
    1. Setting up client with operator account
    2. Creating a fungible token with the operator account as owner
    3. Getting initial token supply
    4. Burning 50 tokens from the total supply
    5. Getting final token supply to verify burn
    """
    client, operator_id, operator_key = setup_client()

    # Create a fungible token with the treasury account as owner and signer
    token_id = create_fungible_token(client, operator_id, operator_key)
    
    # Get and print token supply before burn to show the initial state
    print("\nToken supply before burn:")
    get_token_info(client, token_id)
    
    burn_amount = 40
    
    # Burn 40 tokens out of 100
    receipt = (
        TokenBurnTransaction()
        .set_token_id(token_id)
        .set_amount(burn_amount)
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token burn failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
        
    print(f"Successfully burned {burn_amount} tokens from {token_id}")
    
    # Get and print token supply after burn to show the final state
    print("\nToken supply after burn:")
    get_token_info(client, token_id)
    
if __name__ == "__main__":
    token_burn_fungible()
