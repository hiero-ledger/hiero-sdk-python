"""
uv run examples/query/payment_query.py
python examples/query/payment_query.py
"""
from hiero_sdk_python import (
    Client,
    Hbar,
    ResponseCode,
    TokenCreateTransaction,
    TokenType,
    SupplyType,
)
import sys  


def setup_client():
    """Initialize and set up the client with operator account using env vars."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client, client.operator_account_id, client.operator_private_key


def create_fungible_token(client, operator_id, operator_key):
    """Create a fungible token"""
    print("Creating fungible token...")
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
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    return token_id


def query_payment_example():
    client, operator_id, operator_key = setup_client()
    
    # Create a token to demonstrate
    create_fungible_token(client, operator_id, operator_key)


if __name__ == "__main__":
    query_payment_example()