"""
This example demonstrates how to query file info using the Python SDK.
uv run examples/file/file_info_query.py
python examples/file/file_info_query.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_info_query import FileInfoQuery
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


def create_file(client: Client):
    """Create a test file"""
    file_private_key = PrivateKey.generate_ed25519()

    receipt = (
        FileCreateTransaction()
        .set_keys(
            [file_private_key.public_key(), client.operator_private_key.public_key()]
        )
        .set_contents(b"Hello, this is a test file for querying!")
        .set_file_memo("Test file for query")
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"File creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    file_id = receipt.file_id
    print(f"\nFile created with ID: {file_id}")

    return file_id


def query_file_info():
    """
    Demonstrates querying file info by:
    1. Setting up client with operator account
    2. Creating a test file
    3. Querying the file info
    """
    client = setup_client()

    # Create a test file first
    file_id = create_file(client)

    info = FileInfoQuery().set_file_id(file_id).execute(client)

    print("\nFile Info:")
    print(f"File ID: {info.file_id}")
    print(f"Size: {info.size} bytes")
    print(f"Memo: {info.file_memo}")
    print(f"Expiration Time: {info.expiration_time}")
    print(f"Deleted: {info.is_deleted}")
    print(f"Total key(s): {len(info.keys)}")
    for i, key in enumerate(info.keys, 1):
        print(f"Key {i}: {key.to_string()}")


if __name__ == "__main__":
    query_file_info()
