"""Example of creating an account using a separate ECDSA key for the EVM alias.

This demonstrates a more advanced scenario:
1. Using a 'main' key (e.g., ED25519) to control the account.
2. Using a separate, secondary ECDSA key to generate an EVM alias.
3. Signing the transaction with both keys to link them securely.

Usage:
    uv run examples/account/account_create_transaction_create_with_alias.py
    python examples/account/account_create_transaction_create_with_alias.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    AccountInfoQuery,
    Client,
    Hbar,
    Network,
    PrivateKey,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize client and return operator credentials.

    Returns:
        tuple: A tuple containing (Client, operator_id, operator_key).

    """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key

    except Exception:
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_main_and_alias_keys():
    """Generate the main account key and a separate ECDSA alias key.

    - The 'main' key will be the primary key on the Hedera account (can be ED25519).
    - The 'alias' key must be ECDSA to generate a valid EVM address alias.

    Returns:
        tuple: (main_private_key, alias_private_key)

    """
    print("\nSTEP 1: Generating main account key and separate ECDSA alias key...")

    # Main account key (using standard ED25519)
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


def create_account_with_ecdsa_alias(client, main_private_key, alias_private_key, operator_key):
    """Create an account with a separate ECDSA key as the EVM alias.

    This uses `set_key_with_alias` to map the main key to the alias key.
    The transaction requires signatures from both the alias key (to authorize
    the use of the alias) and the operator (to pay fees).

    Args:
        client: The initialized Client instance.
        main_private_key: The private key for the main account.
        alias_private_key: The private key for the alias (needed for signing).
        operator_key: The operator's private key (payer).

    Returns:
        AccountId: The ID of the newly created account.

    """
    print("\nSTEP 2: Creating the account with the EVM alias from the ECDSA key...")

    alias_public_key = alias_private_key.public_key()

    transaction = AccountCreateTransaction(
        initial_balance=Hbar(5),
        memo="Account with separate ECDSA alias",
    ).set_key_with_alias(main_private_key, alias_public_key)

    # Freeze and sign:
    # - alias_private_key: Required to prove ownership of the ECDSA alias.
    # - operator_key: Required to pay for the transaction.
    transaction = transaction.freeze_with(client).sign(alias_private_key).sign(operator_key)

    response = transaction.execute(client)

    # Safe retrieval of account ID
    new_account_id = response.account_id
    if new_account_id is None:
        try:
            new_account_id = response.get_receipt(client).account_id
        except Exception:
            raise RuntimeError("AccountID not found. Account may not have been created.")

    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client, account_id):
    """Fetch account information from the network."""
    print("\nSTEP 3: Fetching account information...")
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info):
    """Print a summary of the account information."""
    print("--- Account Info ---")
    print(account_info)
    print("--------------------\n")

    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (EVM alias on-chain): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


def main():
    """Run the example workflow."""
    try:
        client, _, operator_key = setup_client()

        main_private_key, alias_private_key = generate_main_and_alias_keys()

        account_id = create_account_with_ecdsa_alias(client, main_private_key, alias_private_key, operator_key)

        account_info = fetch_account_info(client, account_id)

        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
