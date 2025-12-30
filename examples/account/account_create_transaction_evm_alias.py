"""Example of creating an account using an EVM-style alias.

This example demonstrates:
1. Generating an ECDSA key pair (required for EVM compatibility).
2. Deriving the EVM address from the public key.
3. Creating a new Hedera account with that EVM address as its alias.
4. Retrieving the account info to verify the alias.

Usage:
    uv run examples/account/account_create_transaction_evm_alias.py
    python examples/account/account_create_transaction_evm_alias.py
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
    ResponseCode,
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


def generate_alias_key():
    """Generate a new ECDSA key pair and derive its EVM-style alias address.

    EVM aliases on Hedera must be derived from an ECDSA (secp256k1) key pair.
    The EVM address is the last 20 bytes of the keccak256 hash of the public key.

    Returns:
        tuple: (private_key, public_key, evm_address)

    """
    print("\nSTEP 1: Generating a new ECDSA key pair for the account alias...")

    # ECDSA is required for EVM compatibility
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()

    # Compute the EVM address from the public key
    evm_address = public_key.to_evm_address()

    if evm_address is None:
        print("❌ Error: Failed to generate EVM address from public key.")
        sys.exit(1)

    print(f"✅ Generated new ECDSA key pair. EVM Address (alias): {evm_address}")
    return private_key, public_key, evm_address


def create_account_with_alias(client, private_key, public_key, evm_address, operator_key):
    """Create a new Hedera account using the provided EVM-style alias.

    Important: When creating an account with an alias, the transaction must be
    signed by the private key corresponding to that alias. This proves ownership
    of the alias (the EVM address) being claimed.

    Args:
        client: The initialized Client instance.
        private_key: The ECDSA private key for the alias (needed for signing).
        public_key: The public key associated with the alias.
        evm_address: The EVM address string to set as the alias.
        operator_key: The operator's private key (payer).

    Returns:
        AccountId: The ID of the newly created account.

    """
    print("\nSTEP 2: Creating the account with the EVM address alias...")

    transaction = AccountCreateTransaction().set_key(public_key).set_initial_balance(Hbar(5)).set_alias(evm_address)

    # The transaction must be signed by:
    # 1. The new key (to prove we own the alias/public key)
    # 2. The operator key (to pay for the transaction fees)
    transaction = transaction.freeze_with(client).sign(private_key).sign(operator_key)

    response = transaction.execute(client)

    if response.status != ResponseCode.SUCCESS:
        print(f"❌ Account creation failed with status: {ResponseCode(response.status).name}")
        sys.exit(1)

    new_account_id = response.account_id
    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client, account_id):
    """Retrieve detailed information for a given account."""
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info):
    """Print a human-readable summary using native string conversion."""
    print("🧾 Account Info:")
    print(account_info)
    print("")

    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (alias): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


def main():
    """Run the example workflow."""
    # 1. Setup with explicit keys
    client, _, operator_key = setup_client()

    try:
        # 2. Generate Key
        private_key, public_key, evm_address = generate_alias_key()

        # 3. Create Account (Passing operator_key safely)
        new_account_id = create_account_with_alias(client, private_key, public_key, evm_address, operator_key)

        # 4. Fetch Info
        account_info = fetch_account_info(client, new_account_id)

        # 5. Print Summary
        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
