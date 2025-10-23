"""
Create a topic on the Hiero testnet using the Python SDK.
"""
import os
import sys
from typing import Tuple
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    Network,
)

load_dotenv()


def setup_client() -> Tuple[Client, PrivateKey]:
    """Configure client from OPERATOR_ID and OPERATOR_KEY environment variables."""
    network = Network(network='testnet')
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    except (TypeError, ValueError) as e:
        print(f"Error: invalid OPERATOR_ID or OPERATOR_KEY in .env: {e}")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)
    return client, operator_key


def create_new_topic(client: Client, operator_key: PrivateKey):
    """Create a new topic and print the result."""
    print("Creating a new topic...")

    transaction = (
        TopicCreateTransaction(
            memo="Python SDK created topic",
            admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topic_id:
            print(f"Success! Topic created with ID: {receipt.topic_id}")
        else:
            print("Topic creation failed: no topic ID returned.")
            sys.exit(1)
    except Exception as e:
        print(f"Topic creation failed: {e}")
        sys.exit(1)


def main():
    client, operator_key = setup_client()
    create_new_topic(client, operator_key)


if __name__ == "__main__":
    main()
