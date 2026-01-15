"""
uv run examples/query/payment_query.py
python examples/query/payment_query.py
"""
from hiero_sdk_python import (
    Client,
    TokenCreateTransaction,
    TokenType,
    SupplyType,
    AccountBalanceQuery, 
)
import sys


def setup_client():
    """Initialize and set up the client with operator account using env vars."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client, client.operator_account_id, client.operator_private_key


def query_payment_example():
    client, operator_id, operator_key = setup_client()
    

    print("Demonstrating query payment/cost estimation...")

    balance_query = AccountBalanceQuery().set_account_id(operator_id)
    query_cost = balance_query.get_cost(client)
    print(f"Estimated cost for AccountBalanceQuery: {query_cost}")
    
    # Execute the query
    balance = balance_query.execute(client)
    print(f"Account balance: {balance.hbars}")


if __name__ == "__main__":
    query_payment_example()