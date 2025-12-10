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

def create_account_with_fallback_alias(client: Client) -> None:
    """Create an account whose alias is derived from the main ECDSA key."""
    try:
        print("\nSTEP 1: Generating a single ECDSA key pair for the account...")
        account_private_key = PrivateKey.generate("ecdsa")
        account_public_key = account_private_key.public_key()
        evm_address = account_public_key.to_evm_address()

        if evm_address is None:
            print("❌ Error: Failed to generate EVM address from ECDSA public key.")
            sys.exit(1)

        print(f"✅ Account ECDSA public key: {account_public_key}")
        print(f"✅ Derived EVM address:      {evm_address}")

        print("\nSTEP 2: Creating the account using the fallback alias behaviour...")
        transaction = (
            AccountCreateTransaction(
                initial_balance=Hbar(5),
                memo="Account with alias derived from main ECDSA key",
            )
            # Fallback path: only one ECDSA key is provided
            .set_key_with_alias(account_private_key)
        )

        # Freeze & sign with the account key as well
        transaction = (
            transaction.freeze_with(client)
            .sign(account_private_key)
        )

        response = transaction.execute(client)
        new_account_id = response.account_id

        if new_account_id is None:
            raise RuntimeError(
                "AccountID not found in receipt. Account may not have been created."
            )

        print(f"✅ Account created with ID: {new_account_id}\n")

        account_info = (
            AccountInfoQuery()
            .set_account_id(new_account_id)
            .execute(client)
        )

        out = info_to_dict(account_info)
        print("Account Info:")
        print(json.dumps(out, indent=2) + "\n")

        print(
            "✅ contract_account_id (EVM alias on-chain): "
            f"{account_info.contract_account_id}"
        )

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)

def main():
    """Main entry point."""
    client = setup_client()
    create_account_with_fallback_alias(client)

if __name__ == "__main__":
    main()
