"""
uv run examples/consensus/topic_delete_transaction.py
python examples/consensus/topic_delete_transaction.py

Refactored to be more modular:
- topic_delete_transaction() performs the create+delete transaction steps
- main() orchestrates setup and calls helper functions
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicDeleteTransaction,
    Network,
    TopicCreateTransaction,
    ResponseCode,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    print(f"🌐 Connecting to Hedera {network_name}...")
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id_str = os.getenv("OPERATOR_ID")
        operator_key_str = os.getenv("OPERATOR_KEY")
        if not operator_id_str or not operator_key_str:
            print("Error: OPERATOR_ID or OPERATOR_KEY not set in .env file")
            sys.exit(1)
        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("Error: Creating client, Please check your .env file")
        sys.exit(1)


def create_topic(client, operator_key):
    """Create a new topic"""
    print("\nSTEP 1: Creating a Topic...")
    try:
        topic_tx = (
            TopicCreateTransaction(
                memo="Python SDK created topic", admin_key=operator_key.public_key()
            )
            .freeze_with(client)
            .sign(operator_key)
        )
        topic_receipt = topic_tx.execute(client)
        topic_id = topic_receipt.topic_id
        print(f"✅ Success! Created topic: {topic_id}")

        return topic_id
    except Exception as e:
        print(f"Error: Creating topic: {e}")
        sys.exit(1)


def topic_delete_transaction(client, operator_key, topic_id):
    """
    Perform the topic delete transaction for the given topic_id.
    Separated so it can be called independently in tests or other scripts.
    """
    print("\nSTEP 2: Deleting Topic...")
    transaction = (
        TopicDeleteTransaction(topic_id=topic_id).freeze_with(client).sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(
            f"Topic Delete Transaction completed: "
            f"(status: {ResponseCode(receipt.status).name}, "
            f"transaction_id: {receipt.transaction_id})"
        )
        print(f"✅ Success! Topic {topic_id} deleted successfully.")
    except Exception as e:
        print(f"Error: Topic deletion failed: {str(e)}")
        sys.exit(1)


def main():
    """Orchestrator — runs the example start-to-finish"""
    # Config Client
    client, _, operator_key = setup_client()

    # Create a new Topic
    topic_id = create_topic(client, operator_key)

    # Delete the topic
    topic_delete_transaction(client, operator_key, topic_id)


if __name__ == "__main__":
    main()
