"""
This example demonstrates how to delete a file using the Python SDK.
Run with:
uv run examples/file_delete_transaction.py
python examples/file_delete_transaction.py

"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_id import FileId
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
    """Create a test file and return its ID along with the private key"""

    file_private_key = PrivateKey.generate_ed25519()

    receipt = (
        FileCreateTransaction()
        .set_keys(file_private_key.public_key())
        .set_contents(b"Hello, this is a test file that will be deleted!")
        .set_file_memo("Test file for deletion example")
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"File creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    file_id = receipt.file_id
    print(f"File created successfully with ID: {file_id}")

    return file_id, file_private_key


def query_file_info(client: Client, file_id: FileId):
    """Query file info and display the results"""
    info = FileInfoQuery().set_file_id(file_id).execute(client)

    print(info)


def file_delete():
    """
    Demonstrates the complete file lifecycle by:
    1. Creating a file
    2. Querying file info (before deletion)
    3. Deleting the file
    4. Querying file info (after deletion)
    """
    # Setup client
    client = setup_client()

    # Create file
    file_id, file_private_key = create_file(client)

    # Query file info before deletion
    query_file_info(client, file_id)

    # Delete the file
    receipt = (
        FileDeleteTransaction()
        .set_file_id(file_id)
        .freeze_with(client)
        .sign(file_private_key)  # File key is required to delete
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"File deletion failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"\nFile deleted successfully with ID: {file_id}\n")
    print("Check if file is deleted by querying info:")

    # Query file info after deletion
    query_file_info(client, file_id)


if __name__ == "__main__":
    file_delete()
