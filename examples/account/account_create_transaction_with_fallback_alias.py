"""Example: Create an account where the EVM alias is derived from the main ECDSA key.

This demonstrates:
- Passing only an ECDSA PrivateKey to `set_key_with_alias`
- The alias being derived from the main key's EVM address (fallback behaviour)

Usage:
    uv run examples/account/account_create_transaction_with_fallback_alias.py
    python examples/account/account_create_transaction_with_fallback_alias.py
"""

import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    AccountInfo,
    AccountInfoQuery,
    Client,
    Hbar,
    PrivateKey,
)

load_dotenv()


def setup_client() -> Client:
    """Initialize client from environment variables."""
    try:
        client = Client.from_env()
        print(f"Client set up with operator id {client.operator_account_id}")
        return client
    except Exception:
        print("Error: Please check OPERATOR_ID, OPERATOR_KEY, and NETWORK in your .env file.")
        sys.exit(1)


def generate_fallback_key() -> PrivateKey:
    """Generate an ECDSA key pair and validate its EVM address."""
    print("\nSTEP 1: Generating a single ECDSA key pair for the account...")
    account_private_key = PrivateKey.generate("ecdsa")
    account_public_key = account_private_key.public_key()

    # Validate that the key is ECDSA-compatible by deriving the EVM address.
    # The actual alias will be derived by set_key_with_alias() in the next step.
    try:
        evm_address = account_public_key.to_evm_address()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print(f"✅ Account ECDSA public key: {account_public_key}")
    print(f"✅ Derived EVM address:       {evm_address}")

    return account_private_key


def create_account_with_fallback_alias(client: Client, account_private_key: PrivateKey) -> AccountId:
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
        raise RuntimeError("AccountID not found in receipt. Account may not have been created.")

    print(f"✅ Account created with ID: {new_account_id}\n")

    return new_account_id


def fetch_account_info(client: Client, account_id: AccountId) -> AccountInfo:
    """Fetch account info for the given account ID."""
    print("\nSTEP 3: Fetching account information...")

    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info: AccountInfo) -> None:
    """Print an account summary (including EVM alias)."""
    print("\nSTEP 4: Printing account EVM alias and summary...")
    print("🧾 Account Info:")
    print(account_info)
    print("")

    if account_info.contract_account_id is not None:
        print(f"✅ contract_account_id (EVM alias on-chain): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


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
