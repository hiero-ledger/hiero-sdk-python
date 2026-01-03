"""
uv run examples/consensus/topic_create_transaction.py
python examples/consensus/topic_create_transaction.py
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

# Load environment variables from .env file
load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> Tuple[Client, PrivateKey]:
    """
    Sets up and configures the Hiero client for the testnet.
    Reads OPERATOR_ID and OPERATOR_KEY from environment variables.
    """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")

    # Check if the environment variables are loaded correctly
    if not operator_id_str or not operator_key_str:
        print("Error: OPERATOR_ID or OPERATOR_KEY not found in environment.")
        print("Please create a .env file in the project's root directory with:")
        print("\nOPERATOR_ID=your_id_here")
        print("OPERATOR_KEY=your_key_here\n")
        sys.exit(1)

    try:
        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)
    except (TypeError, ValueError) as e:
        print(f"Error: Invalid OPERATOR_ID or OPERATOR_KEY format: {e}")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")
    return client, operator_key


def create_topic(client: Client, operator_key: PrivateKey):
    """
    Builds, signs, and executes a new topic creation transaction.
    """
    transaction = (
        TopicCreateTransaction(
            memo="Python SDK created topic", admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topic_id:
            print(f"Success! Topic created with ID: {receipt.topic_id}")
        else:
            print("Topic creation failed: Topic ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")
        sys.exit(1)


def main():
    """
    Main workflow to set up the client and create a new topic.
    """
    client, operator_key = setup_client()
    create_topic(client, operator_key)


if __name__ == "__main__":
    main()
