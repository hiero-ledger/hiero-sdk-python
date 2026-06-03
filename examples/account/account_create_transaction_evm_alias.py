"""

Example: Create an account using an EVM-style alias (evm_address).

This example demonstrates:
1. Generating an ECDSA key pair (required for EVM compatibility).
2. Deriving the EVM address from the public key.
3. Creating a new Hedera account with that EVM address as its alias.
4. Retrieving the account info to verify the alias.

Usage:
    uv run examples/account/account_create_transaction_evm_alias.py
    python examples/account/account_create_transaction_evm_alias.py
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
    PublicKey,
)


load_dotenv()


def setup_client() -> Client:
    """Initialize client from environment variables."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def generate_alias_key() -> tuple[PrivateKey, PublicKey]:
    """

    Generate a new ECDSA key pair for the account.

    EVM aliases on Hedera must be derived from an ECDSA (secp256k1) key pair.
    The EVM address is the last 20 bytes of the keccak256 hash of the public key.
    The alias itself is derived automatically by
    ``AccountCreateTransaction.set_key_with_alias`` in the next step, so this
    helper only needs to return the key pair.

    Returns:
        tuple: A 2-tuple of:
            - private_key: The newly generated ECDSA private key.
            - public_key: The public key corresponding to the private key.
    """
    print("\nSTEP 1: Generating a new ECDSA key pair for the account alias...")

    # ECDSA is required for EVM compatibility
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()

    # Validate that the key is ECDSA-compatible by deriving the EVM address.
    # The actual alias will be derived by set_key_with_alias() in the next step.
    try:
        evm_address = public_key.to_evm_address()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print(f"✅ Generated new ECDSA key pair. EVM Address (alias): {evm_address}")
    return private_key, public_key


def create_account_with_alias(client: Client, private_key: PrivateKey, public_key: PublicKey) -> AccountId:
    """

    Create a new Hedera account using an EVM-style alias.

    ``set_key_with_alias`` sets the account key and derives the EVM-address alias
    from the same public key in a single call, replacing the deprecated pairing
    of ``set_key`` and ``set_alias``.

    Important: When creating an account with an alias, the transaction must be
    signed by the private key corresponding to that alias. This proves ownership
    of the alias (the EVM address) being claimed.

    Args:
        client: An initialized `Client` instance with an operator set.
        private_key: The newly generated `PrivateKey` corresponding to the
            alias public key, used to sign the transaction.
        public_key: The public key associated with `private_key`, which is
            set as the new account's key and used to derive the alias.

    Returns:
        The `AccountId` of the newly created account.

    """
    print("\nSTEP 2: Creating the account with the EVM address alias...")

    transaction = AccountCreateTransaction().set_key_with_alias(public_key).set_initial_balance(Hbar(5))

    # Sign with new key (required for alias)
    # The client.execute() call below will attach the operator signature automatically.
    transaction = transaction.freeze_with(client).sign(private_key)

    # Execute the transaction
    response = transaction.execute(client)

    # Safe retrieval of account ID
    new_account_id = response.account_id
    if new_account_id is None:
        raise RuntimeError("AccountID not found in receipt. Account may not have been created.")

    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client: Client, account_id: AccountId) -> AccountInfo:
    """Retrieve detailed information for a given account from the Hedera network."""
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info: AccountInfo) -> None:
    """Print a human-readable summary of Hedera account information."""
    print("🧾 Account Info:")
    print(account_info)
    print("")

    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (alias): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


def main():
    """Orchestrate the example workflow."""
    client = setup_client()
    try:
        private_key, public_key = generate_alias_key()

        new_account_id = create_account_with_alias(client, private_key, public_key)

        account_info = fetch_account_info(client, new_account_id)

        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
