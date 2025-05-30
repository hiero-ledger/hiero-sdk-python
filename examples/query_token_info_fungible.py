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
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
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
        .set_freeze_key(operator_key)
        .execute(client)
    )
    
    # Check if token creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get token ID from receipt
    token_id = receipt.tokenId
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def query_token_info():
    """
    Demonstrates the token info query functionality by:
    1. Creating a fungible token
    2. Querying the token's information using TokenInfoQuery
    3. Printing the token details of the TokenInfo object
    """
    client, operator_id, operator_key = setup_client()
    token_id = create_fungible_token(client, operator_id, operator_key)
        
    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"Fungible token info: {info}")

if __name__ == "__main__":
    query_token_info()
