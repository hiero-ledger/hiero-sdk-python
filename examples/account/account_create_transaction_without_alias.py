"""
Example: Create an account without using any alias.

This demonstrates:
- Using `set_key_without_alias` so that no EVM alias is set
- The resulting `contract_account_id` being the zero-padded value

Usage:
- uv run -m examples.account.account_create_transaction_without_alias
- python -m examples.account.account_create_transaction_without_alias
(we use -m because we use the util `info_to_dict`)
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


def setup_client():
    """Setup Client."""
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


def create_account_without_alias(client: Client) -> None:
    """Create an account explicitly without an alias."""
    try:
        print("\nSTEP 1: Generating a key pair for the account (no alias)...")
        account_private_key = PrivateKey.generate()
        account_public_key = account_private_key.public_key()

        print(f"✅ Account public key (no alias): {account_public_key}")

        print("\nSTEP 2: Creating the account without setting any alias...")

        transaction = AccountCreateTransaction(
            initial_balance=Hbar(5),
            memo="Account created without alias",
        ).set_key_without_alias(account_private_key)

        transaction = transaction.freeze_with(client).sign(account_private_key)

        response = transaction.execute(client)
        new_account_id = response.account_id

        if new_account_id is None:
            raise RuntimeError(
                "AccountID not found in receipt. Account may not have been created."
            )

        print(f"✅ Account created with ID: {new_account_id}\n")

        account_info = AccountInfoQuery().set_account_id(new_account_id).execute(client)

        out = info_to_dict(account_info)
        print("Account Info:")
        print(json.dumps(out, indent=2) + "\n")

        print(
            "✅ contract_account_id (no alias, zero-padded): "
            f"{account_info.contract_account_id}"
        )

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


def main():
    """Main entry point."""
    client = setup_client()
    create_account_without_alias(client)


if __name__ == "__main__":
    main()
