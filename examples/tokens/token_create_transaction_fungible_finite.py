"""
This is a simple example of how to create a finite fungible token using setting methods.

It:
1. Loads environment variables.
2. Sets up a client and creates a token with the given parameters.
3. Executes the token creation and prints the result.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY (mandatory)
- ADMIN_KEY, SUPPLY_KEY, FREEZE_KEY, PAUSE_KEY (optional)

Dependencies:
- dotenv
- hiero_sdk_python

Usage:
uv run examples/tokens/token_create_transaction_fungible_finite.py
python examples/tokens/token_create_transaction_fungible_finite.py
"""

import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    Network,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType


def parse_optional_key(key_str):
    """Parse an optional private key from environment variables."""
    if not key_str or key_str.startswith('<') or key_str.endswith('>'):
        return None
    try:
        return PrivateKey.from_string_ed25519(key_str)
    except Exception:
        return None

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


def load_optional_keys():
    """Load optional keys (admin, supply, freeze, pause)."""
    admin_key = parse_optional_key(os.getenv('ADMIN_KEY'))
    supply_key = parse_optional_key(os.getenv('SUPPLY_KEY'))
    freeze_key = parse_optional_key(os.getenv('FREEZE_KEY'))
    pause_key = parse_optional_key(os.getenv('PAUSE_KEY'))
    return admin_key, supply_key, freeze_key, pause_key


def build_transaction(client, operator_id, keys):
    """Build and freeze the token creation transaction."""
    admin_key, supply_key, freeze_key, pause_key = keys

    transaction = (
        TokenCreateTransaction()
        .set_token_name("FiniteFungibleToken")
        .set_token_symbol("FFT")
        .set_decimals(2)
        .set_initial_supply(10)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .freeze_with(client)
    )

    if admin_key:
        transaction.set_admin_key(admin_key)
    if supply_key:
        transaction.set_supply_key(supply_key)
    if freeze_key:
        transaction.set_freeze_key(freeze_key)
    if pause_key:
        transaction.set_pause_key(pause_key)

    return transaction


def execute_transaction(transaction, client, operator_key, admin_key):
    """Sign and execute the transaction."""
    transaction.sign(operator_key)
    if admin_key:
        transaction.sign(admin_key)

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.token_id:
            print(f"Finite fungible token created with ID: {receipt.token_id}")
        else:
            print("Finite fungible token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)


def create_token_fungible_finite():
    """Main function to create finite fungible token."""
    client, operator_id, operator_key = setup_client()
    keys = load_optional_keys()
    transaction = build_transaction(client, operator_id, keys)
    execute_transaction(transaction, client, operator_key, keys[0])


if __name__ == "__main__":
    create_token_fungible_finite()
