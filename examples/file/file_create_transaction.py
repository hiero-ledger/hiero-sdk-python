"""
Run with:
uv run examples/file_create_transaction.py
python examples/file_create_transaction.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def file_create():
    """
    Demonstrates creating a file on the network by:
    1. Setting up client with operator account
    2. Creating a file with a private key
    3. Creating a new file
    """
    client = setup_client()

    file_private_key = PrivateKey.generate_ed25519()

    # Create file
    receipt = (
        FileCreateTransaction()
        .set_keys(
            file_private_key.public_key()
        )  # Set the keys required to sign any modifications to this file
        .set_contents(b"Hello, this is the content of my file on Hedera!")
        .set_file_memo("My first file on Hedera")
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )

    # Check if the transaction was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"File creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    file_id = receipt.file_id
    print(f"File created successfully with ID: {file_id}")


if __name__ == "__main__":
    file_create()
