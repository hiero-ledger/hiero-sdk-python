"""
uv run examples/query/payment_query.py
python examples/query/payment_query.py
"""

import sys

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction


def setup_client():
    """Initialize client using environment configuration"""
    print("Connecting to Hedera network using environment configuration...")

    client = Client.from_env()

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    if not operator_id or not operator_key:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY must be set in the environment"
        )

    print(f"Client set up with operator id {operator_id}")
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
        print(
            f"Fungible token creation failed with status: "
            f"{ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")

    return token_id


def demonstrate_zero_cost_balance_query(client, account_id):
    """
    Demonstrate cost calculation for queries that don't require payment.
    """
    print("\nQueries that DON'T require payment:\n")

    print("When no payment is set:")
    query_no_payment = CryptoGetAccountBalanceQuery().set_account_id(account_id)

    cost_no_payment = query_no_payment.get_cost(client)
    print(f"Cost: {cost_no_payment} Hbar")
    print("Expected: 0 Hbar (payment not required)")

    print("\nExecuting query without payment...")
    result = query_no_payment.execute(client)
    print("Query executed successfully!")
    print(f"    Account balance (only hbars): {result.hbars}")

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

    print("\nExecuting query with custom payment...")
    result = query_with_payment.execute(client)
    print("Query executed successfully!")
    print(f"    Account balance (only hbars): {result.hbars}")


def demonstrate_payment_required_queries(client, token_id):
    """
    Demonstrate cost calculation for queries that require payment.
    """
    print("\nQueries that DO require payment:\n")

    print("When no payment is set:")
    query_no_payment = TokenInfoQuery().set_token_id(token_id)

    print("Asking network for query cost...")
    cost_from_network = query_no_payment.get_cost(client)
    print(f"Cost: {cost_from_network} Hbar")

    print("\nExecuting query with network-determined cost...")
    result = query_no_payment.execute(client)
    print("Query executed successfully!")
    print(f"    Token info: {result}")

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

    print("\nExecuting query with custom payment...")
    result = query_with_payment.execute(client)
    print("Query executed successfully!")
    print(f"    Token info: {result}")

    print("\nCost comparison:")
    print(f"Network-determined cost: {cost_from_network} Hbar")
    print(f"Custom payment: {custom_payment} Hbar")


def query_payment():
    """
    Demonstrates the query payment behavior.
    """
    client, operator_id, operator_key = setup_client()

    token_id = create_fungible_token(client, operator_id, operator_key)

    demonstrate_zero_cost_balance_query(client, operator_id)
    demonstrate_payment_required_queries(client, token_id)


if __name__ == "__main__":
    query_payment()
