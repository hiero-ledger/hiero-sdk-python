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
    """Setup Hedera Client."""
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


def generate_account_key():
    """Generate a private/public key pair for the new account."""
    print("\nSTEP 1: Generating a key pair for the account (no alias)...")

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    print(f" Account public key (no alias): {public_key}")

    return private_key, public_key

def create_account_without_alias(client: Client, private_key: PrivateKey):
    """Create a Hedera account without setting any alias."""
    print("\nSTEP 2: Creating the account without setting any alias...")

    try:
        transaction = (
            AccountCreateTransaction(
                initial_balance=Hbar(5),
                memo="Account created without alias",
            )
            .set_key_without_alias(private_key)
        )

        transaction = transaction.freeze_with(client).sign(private_key)
        response = transaction.execute(client)

        if response.account_id is None:
            raise RuntimeError(
                "AccountID not found in receipt. Account may not have been created."
            )

        new_account_id = response.account_id
        print(f" Account created with ID: {new_account_id}\n")

        return new_account_id

    except Exception as error:
        print(f" Error creating account: {error}")
        sys.exit(1)


def fetch_account_info(client: Client, account_id):
    """Fetch and return Hedera account info."""
    print("Fetching account info...")

    try:
        account_info = (
            AccountInfoQuery()
            .set_account_id(account_id)
            .execute(client)
        )

        return account_info

    except Exception as error:
        print(f" Error fetching account info: {error}")
        sys.exit(1)

def print_account_summary(account_info):
    """Print account information in a clean JSON format."""
    out = info_to_dict(account_info)

    print("\nAccount Info:")
    print(json.dumps(out, indent=2))

    print(
        "\n contract_account_id (no alias, zero-padded): "
        f"{account_info.contract_account_id}"
    )
def main():
    client = setup_client()

    private_key, public_key = generate_account_key()

    new_account_id = create_account_without_alias(client, private_key)

    account_info = fetch_account_info(client, new_account_id)

    print_account_summary(account_info)


if __name__ == "__main__":
    main()
