"""Example: Create an account using a separate ECDSA key for the EVM alias.

This demonstrates:
- Using a "main" key for the account
- Using a separate ECDSA public key as the EVM alias
- The need to sign the transaction with the alias private key

Usage:
    uv run examples/account/account_create_transaction_create_with_alias.py
    python examples/account/account_create_transaction_create_with_alias.py
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


def generate_main_and_alias_keys() -> tuple[PrivateKey, PrivateKey]:
    """Generate the main account key and a separate ECDSA alias key.

    Returns:
        tuple: (main_private_key, alias_private_key)

    """
    print("\nSTEP 1: Generating main account key and separate ECDSA alias key...")

    # Main account key (can be any key type, here ed25519)
    main_private_key = PrivateKey.generate()
    main_public_key = main_private_key.public_key()

    # Separate ECDSA key used only for the EVM alias
    alias_private_key = PrivateKey.generate("ecdsa")
    alias_public_key = alias_private_key.public_key()
    alias_evm_address = alias_public_key.to_evm_address()

    if alias_evm_address is None:
        print("❌ Error: Failed to generate EVM address from alias ECDSA key.")
        sys.exit(1)

    print(f"✅ Main account public key:  {main_public_key}")
    print(f"✅ Alias ECDSA public key:   {alias_public_key}")
    print(f"✅ Alias EVM address:        {alias_evm_address}")

    return main_private_key, alias_private_key


def create_account_with_ecdsa_alias(
    client: Client, main_private_key: PrivateKey, alias_private_key: PrivateKey
) -> AccountId:
    """Create an account with a separate ECDSA key as the EVM alias.

    This uses `set_key_with_alias` to map the main key to the alias key.
    The transaction requires signatures from both the alias key (to authorize
    the use of the alias) and the operator (to pay fees).

    Args:
        client: The Hedera client.
        main_private_key: The main account private key.
        alias_private_key: The ECDSA private key for the EVM alias.

    Returns:
        AccountId: The newly created account ID.

    """
    print("\nSTEP 2: Creating the account with the EVM alias from the ECDSA key...")

    alias_public_key = alias_private_key.public_key()

    # Use the helper that accepts both the main key and the ECDSA alias key
    transaction = AccountCreateTransaction(
        initial_balance=Hbar(5),
        memo="Account with separate ECDSA alias",
    ).set_key_with_alias(main_private_key, alias_public_key)

    # Freeze and sign:
    # - operator key signs as payer (handled by client.execute)
    # - alias private key MUST sign to authorize the alias
    transaction = transaction.freeze_with(client).sign(alias_private_key)

    response = transaction.execute(client)

    # Safe retrieval of account ID
    new_account_id = response.account_id
    if new_account_id is None:
        raise RuntimeError("AccountID not found in receipt. Account may not have been created.")

    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client: Client, account_id: AccountId) -> AccountInfo:
    """Fetch account information from the network.

    Args:
        client: The Hedera client.
        account_id: The account ID to query.

    Returns:
        AccountInfo: The account info object.

    """
    print("\nSTEP 3: Fetching account information...")
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info: AccountInfo) -> None:
    """Print a summary of the account information.

    Args:
        account_info: The account info object to display.

    """
    print("--- Account Info ---")
    print(account_info)
    print("--------------------\n")

    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (EVM alias on-chain): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


def main():
    """Execute the example workflow."""
    try:
        client = setup_client()
        main_private_key, alias_private_key = generate_main_and_alias_keys()
        account_id = create_account_with_ecdsa_alias(client, main_private_key, alias_private_key)
        account_info = fetch_account_info(client, account_id)
        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
