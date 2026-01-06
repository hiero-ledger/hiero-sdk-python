"""
Example: Create an account without using any alias.

This demonstrates:
- Using `set_key_without_alias` so that no EVM alias is set
- The resulting `contract_account_id` being the zero-padded value

Usage:
- uv run python examples/account/account_create_transaction_without_alias.py
- python examples/account/account_create_transaction_without_alias.py
"""

from typing import Tuple
import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    PublicKey,
    AccountCreateTransaction,
    AccountInfoQuery,
    AccountId,
    AccountInfo,
    Hbar,
    ResponseCode,
)

def setup_client() -> Client:
    """Setup Client."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def generate_account_key() -> Tuple[PrivateKey, PublicKey]:
    """Generate a key pair for the account."""
    print("\nSTEP 1: Generating a key pair for the account (no alias)...")
    account_private_key = PrivateKey.generate()
    account_public_key = account_private_key.public_key()
    print(f"✅ Account public key (no alias): {account_public_key}")
    return account_private_key, account_public_key

def create_account_without_alias(client: Client, account_public_key: PublicKey, account_private_key: PrivateKey) -> AccountId:
    """Create an account without setting any alias."""
    print("\nSTEP 2: Creating the account without setting any alias...")
    
    transaction = (
        AccountCreateTransaction(
            initial_balance=Hbar(5),
            memo="Account created without alias",
        )
        .set_key_without_alias(account_public_key)
        .freeze_with(client)
        .sign(account_private_key)
    )

    response = transaction.execute(client)

    if response.status != ResponseCode.SUCCESS:
        raise RuntimeError(
            f"Transaction failed with status: {response.status.name}"
        )

    new_account_id = response.account_id

    if new_account_id is None:
        raise RuntimeError(
            "AccountID not found in receipt. Account may not have been created."
        )

    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id

def fetch_account_info(client: Client, account_id: AccountId) -> AccountInfo:
    """Fetch account information."""
    account_info = (
        AccountInfoQuery()
        .set_account_id(account_id)
        .execute(client)
    )
    return account_info

def main() -> None:
    """Main entry point."""
    try:
        client = setup_client()
        account_private_key, account_public_key = generate_account_key()
        new_account_id = create_account_without_alias(client, account_public_key, account_private_key)
        account_info = fetch_account_info(client, new_account_id)
        print("\nAccount Info:")
        print(account_info)
        print(
            "\n✅ contract_account_id (no alias, zero-padded): "
            f"{account_info.contract_account_id}"
        )
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
