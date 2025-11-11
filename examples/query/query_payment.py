"""
uv run examples/query_payment.py
python examples/query_payment.py

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
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
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
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

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
        print(f"Fungible token creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def demonstrate_zero_cost_balance_query(client, account_id):
    """
    Demonstrate cost calculation for queries that don't require payment.
    
    CryptoGetAccountBalanceQuery is an example of a query that doesn't require payment.
    For such queries:
    - get_cost() returns 0 Hbar when no payment is set
    - get_cost() returns the set payment amount when payment is set
    """
    print("\nQueries that DON'T require payment:\n")
    
    # Case 1: No payment set - should return 0 Hbar cost
    print("When no payment is set:")
    query_no_payment = CryptoGetAccountBalanceQuery().set_account_id(account_id)
    
    cost_no_payment = query_no_payment.get_cost(client)
    print(f"Cost: {cost_no_payment} Hbar")
    print("Expected: 0 Hbar (payment not required)")
    
    # Execute the query (should work without payment)
    print("\nExecuting query without payment...")
    result = query_no_payment.execute(client)
    print(f"Query executed successfully!")
    print(f"    Account balance (only hbars): {result.hbars}")
    
    # Case 2: Payment set - should return the set payment amount
    print("\nWhen custom payment is set:")
    custom_payment = Hbar(2)
    query_with_payment = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(account_id)
        .set_query_payment(custom_payment)
    )
    
    cost_with_payment = query_with_payment.get_cost(client)
    print(f"Cost: {cost_with_payment} Hbar")
    print(f"Expected: {custom_payment} Hbar")
    
    # Execute the query (should work with custom payment)
    print("\nExecuting query with custom payment...")
    result = query_with_payment.execute(client)
    print(f"Query executed successfully!")
    print(f"    Account balance (only hbars): {result.hbars}")

def demonstrate_payment_required_queries(client, token_id):
    """
    Demonstrate cost calculation for queries that require payment.
    
    TokenInfoQuery is an example of a query that requires payment.
    For such queries:
    - get_cost() asks the network for the actual cost when no payment is set
    - get_cost() returns the set payment amount when payment is set
    """
    print("\nQueries that DO require payment:\n")
    
    # Case 1: No payment set - should ask network for cost
    print("When no payment is set:")
    query_no_payment = TokenInfoQuery().set_token_id(token_id)
    
    print("Asking network for query cost...")
    cost_from_network = query_no_payment.get_cost(client)
    print(f"Cost: {cost_from_network} Hbar")
    print("This is the actual cost calculated by the network")
    
    # Execute the query (should work with network-determined cost)
    print("\nExecuting query with network-determined cost...")
    result = query_no_payment.execute(client)
    print(f"Query executed successfully!")
    print(f"    Token info: {result}")
    
    # Case 2: Payment set - should return the set payment amount
    print("\nWhen custom payment is set:")
    custom_payment = Hbar(2)
    query_with_payment = (
        TokenInfoQuery()
        .set_token_id(token_id)
        .set_query_payment(custom_payment)
    )
    
    cost_with_payment = query_with_payment.get_cost(client)
    print(f"Cost: {cost_with_payment} Hbar")
    print(f"Expected: {custom_payment} Hbar")
    
    # Execute the query (should work with custom payment)
    print("\nExecuting query with custom payment...")
    result = query_with_payment.execute(client)
    print(f"Query executed successfully!")
    print(f"    Token info: {result}")
    
    # Case 3: Compare network cost vs custom payment
    print("\nCost comparison:")
    print(f"Network-determined cost: {cost_from_network} Hbar")
    print(f"Custom payment: {custom_payment} Hbar")

def query_payment():
    """
    Demonstrates the query payment by:
    1. Setting up client with operator account
    2. Creating a fungible token with the operator account as owner
    3. Demonstrating queries that don't require payment (CryptoGetAccountBalanceQuery)
    4. Demonstrating queries that do require payment (TokenInfoQuery)
    5. Comparing network-determined cost vs custom payment amount
    """
    client, operator_id, operator_key = setup_client()
    token_id = create_fungible_token(client, operator_id, operator_key)
    
    demonstrate_zero_cost_balance_query(client, operator_id)
    demonstrate_payment_required_queries(client, token_id)

if __name__ == "__main__":
    query_payment()
