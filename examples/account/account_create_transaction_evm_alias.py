# uv run -m examples.account.account_create_transaction_evm_alias
# python -m examples.account.account_create_transaction_evm_alias
"""
Example: Create an account using an EVM-style alias (evm_address).
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
    ResponseCode,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # Get the operator account from the .env file
    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        # Set the operator (payer) account for the client
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client
    except Exception:
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_alias_key():
    """
    Generate a new ECDSA key pair and derive its EVM-style alias address.
    This function creates a new ECDSA private/public key pair and derives the
    corresponding EVM address (alias) from the public key. If the EVM address
    cannot be generated, the process is terminated.
    Returns:
        tuple: A 3-tuple of:
            - private_key: The newly generated ECDSA private key.
            - public_key: The public key corresponding to the private key.
            - evm_address (str): The derived EVM address to be used as an alias.
    """
    print("\nSTEP 1: Generating a new ECDSA key pair for the account alias...")
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    evm_address = public_key.to_evm_address()
    if evm_address is None:
        print("❌ Error: Failed to generate EVM address from public key.")
        sys.exit(1)
    print(f"✅ Generated new ECDSA key pair. EVM Address (alias): {evm_address}")
    return private_key, public_key, evm_address


def create_account_with_alias(client, private_key, public_key, evm_address):
    """
    Create a new Hedera account using the provided EVM-style alias.
    Args:
        client: An initialized `Client` instance with an operator set, used to
            freeze, sign, and execute the account creation transaction.
        private_key: The newly generated `PrivateKey` corresponding to the
            alias public key, used to sign the transaction.
        public_key: The public key associated with `private_key`, which is
            set as the new account's key.
        evm_address: The EVM-style alias (derived from `public_key`) to assign
            to the new account.
    Returns:
        The `AccountId` of the newly created account.
    """
    print("\nSTEP 2: Creating the account with the EVM address alias...")
    transaction = (
        AccountCreateTransaction()
        .set_key(public_key)
        .set_initial_balance(Hbar(5))
        .set_alias(evm_address)
    )

    # Sign the transaction with both the new key and the operator key
    transaction = (
        transaction.freeze_with(client)
        .sign(private_key)
        .sign(client.operator_private_key)
    )

    # Execute the transaction
    response = transaction.execute(client)

    # Validate the receipt status before accessing account_id
    if response.status != ResponseCode.SUCCESS:
        print(
            f"❌ Account creation failed with status: "
            f"{ResponseCode(response.status).name}"
        )
        sys.exit(1)

    new_account_id = response.account_id
    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id


def fetch_account_info(client, account_id):
    """
    Retrieve detailed information for a given account from the Hedera network.
    Args:
        client: An initialized `Client` instance configured with an operator.
        account_id: The identifier of the account whose information is being queried.
    Returns:
        The account information object returned by `AccountInfoQuery.execute(client)`.
    """
    return AccountInfoQuery().set_account_id(account_id).execute(client)


def print_account_summary(account_info):
    """
    Print a human-readable summary of Hedera account information.
    Args:
        account_info: The account information object returned by `AccountInfoQuery`,
            containing fields such as the account ID and optional contract account
            ID (EVM alias) to be displayed.
    """
    out = info_to_dict(account_info)
    print("🧾 Account Info:")
    print(json.dumps(out, indent=2) + "\n")
    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (alias): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")


def main():
    """
    Orchestrate the example workflow for creating an account using an EVM-style alias.
    This function:
      1. Sets up the Hedera client using operator credentials from the environment.
      2. Generates a new ECDSA key pair and derives its EVM address for use as an alias.
      3. Creates a new account with the generated alias and an initial HBAR balance.
      4. Fetches the newly created account's information from the network.
      5. Prints a human-readable summary of the account details, including the contract account ID alias.
    Any unexpected errors are caught and reported before the process exits with a non-zero status.
    """
    client = setup_client()
    try:
        private_key, public_key, evm_address = generate_alias_key()

        new_account_id = create_account_with_alias(
            client, private_key, public_key, evm_address
        )

        account_info = fetch_account_info(client, new_account_id)

        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
