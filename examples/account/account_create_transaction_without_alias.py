"""
Example: Create an account without using any alias.

This demonstrates:
- Using `set_key_without_alias` so that no EVM alias is set
- The resulting `contract_account_id` being the zero-padded value
"""

import os
import sys
import json
from dotenv import load_dotenv

from examples.utils import info_to_dict

from hiero_sdk_python import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    AccountInfoQuery,
    Network,
    AccountId,
    Hbar,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> Client:
    """Initialize and return a Hedera client."""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")

    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)

        print(f"Client set up with operator id {client.operator_account_id}")
        return client

    except Exception:
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_account_key() -> PrivateKey:
    """Generate and return a private key for the new account."""
    print("\nSTEP 1: Generating a key pair for the account (no alias)...")

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    print(f"✅ Account public key (no alias): {public_key}")
    return private_key


def create_account_without_alias(client: Client, private_key: PrivateKey):
    """Create an account on Hedera without setting an alias."""
    print("\nSTEP 2: Creating the account without setting any alias...")

    transaction = (
        AccountCreateTransaction(
            initial_balance=Hbar(5),
            memo="Account created without alias",
        )
        .set_key_without_alias(private_key)
        .freeze_with(client)
        .sign(private_key)
    )

    response = transaction.execute(client)
    account_id = response.account_id

    if account_id is None:
        raise RuntimeError(
            "AccountID not found in receipt. Account may not have been created."
        )

    print(f"✅ Account created with ID: {account_id}\n")
    return account_id


def fetch_account_info(client: Client, account_id):
    """Fetch and return account information."""
    return (
        AccountInfoQuery()
        .set_account_id(account_id)
        .execute(client)
    )


def print_account_summary(account_info) -> None:
    """Print account details and contract account ID."""
    out = info_to_dict(account_info)

    print("Account Info:")
    print(json.dumps(out, indent=2) + "\n")

    print(
        "✅ contract_account_id (no alias, zero-padded): "
        f"{account_info.contract_account_id}"
    )


def main() -> None:
    """Main entry point."""
    try:
        client = setup_client()
        account_key = generate_account_key()
        account_id = create_account_without_alias(client, account_key)
        account_info = fetch_account_info(client, account_id)
        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
