"""
Example: Create an account where the EVM alias is derived from the main ECDSA key.

This demonstrates:
- Passing only an ECDSA PrivateKey to `set_key_with_alias`
- The alias being derived from the main key's EVM address (fallback behaviour)

Usage:
- uv run -m examples.account.account_create_transaction_with_fallback_alias
- python -m examples.account.account_create_transaction_with_fallback_alias
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


def generate_fallback_key() -> PrivateKey:
    """Generate an ECDSA key pair and validate its EVM address."""
    print("\nSTEP 1: Generating a single ECDSA key pair for the account...")
    account_private_key = PrivateKey.generate("ecdsa")
    account_public_key = account_private_key.public_key()
    evm_address = account_public_key.to_evm_address()

    if evm_address is None:
        print("❌ Error: Failed to generate EVM address from ECDSA public key.")
        sys.exit(1)

    print(f"✅ Account ECDSA public key: {account_public_key}")
    print(f"✅ Derived EVM address:      {evm_address}")
    return account_private_key


def create_account_with_fallback_alias(
    client: Client, account_private_key: PrivateKey
) -> AccountId:
    """Create an account whose alias is derived from the provided ECDSA key."""
    print("\nSTEP 2: Creating the account using the fallback alias behaviour...")
    transaction = AccountCreateTransaction(
        initial_balance=Hbar(5),
        memo="Account with alias derived from main ECDSA key",
    ).set_key_with_alias(account_private_key)

    transaction = transaction.freeze_with(client).sign(account_private_key)

    response = transaction.execute(client)
    new_account_id = response.account_id

    if new_account_id is None:
        raise RuntimeError(
            "AccountID not found in receipt. Account may not have been created."
        )

    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client: Client, account_id: AccountId):
    """Fetch account info for the given account ID."""
    print("\nSTEP 3: Fetching account information...")
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info) -> None:
    """Print an account summary (including EVM alias)."""
    print("\nSTEP 4: Printing account EVM alias and summary...")
    out = info_to_dict(account_info)
    print("Account Info:")
    print(json.dumps(out, indent=2) + "\n")
    print(
        "✅ contract_account_id (EVM alias on-chain): "
        f"{account_info.contract_account_id}"
    )


def main():
    """Main entry point."""
    client = setup_client()
    try:
        account_private_key = generate_fallback_key()
        new_account_id = create_account_with_fallback_alias(client, account_private_key)
        account_info = fetch_account_info(client, new_account_id)
        print_account_summary(account_info)
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
