import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network="testnet")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_file(client):
    """Create a test file"""
    file_private_key = PrivateKey.generate_ed25519()

    receipt = (
        FileCreateTransaction()
        .set_keys(file_private_key.public_key())
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

    return file_id, file_private_key


def query_file_info(client, file_id):
    info = FileInfoQuery().set_file_id(file_id).execute(client)

    print(info)


def file_update():
    """
    Demonstrates querying file info by:
    1. Setting up client with operator account
    2. Creating a test file
    3. Querying the file info
    4. Updating the file info
    5. Querying the file info again
    """
    client = setup_client()

    # Create a test file first
    file_id, file_private_key = create_file(client)

    print("File info before update:")
    # Query the file info
    query_file_info(client, file_id)

    # Generate a new private key that will add to the existing key
    new_private_key = PrivateKey.generate_ed25519()

    # Update the file
    receipt = (
        FileUpdateTransaction()
        .set_file_id(file_id)
        .set_keys([file_private_key.public_key(), new_private_key.public_key()])
        .set_contents(b"Updated contents!")
        .set_file_memo("Updated memo!")
        .freeze_with(client)
        .sign(new_private_key)
        .sign(file_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"File update failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("File info after update:")
    # Query the file info again
    query_file_info(client, file_id)


if __name__ == "__main__":
    file_update()
