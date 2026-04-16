"""

Example demonstrating topic message submit transaction.

uv run examples/consensus/topic_message_submit_transaction.py
python examples/consensus/topic_message_submit_transaction.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    Client,
    Network,
    PrivateKey,
    ResponseCode,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
)


load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> tuple[Client, AccountId, PrivateKey]:
    """Setup Client."""
    client = Client.from_env()

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")

    return client, operator_id, operator_key


def create_topic(client, operator_key):
    """Create a new topic."""
    print("\nSTEP 1: Creating a Topic...")
    try:
        topic_tx = (
            TopicCreateTransaction(memo="Python SDK created topic", admin_key=operator_key.public_key())
            .freeze_with(client)
            .sign(operator_key)
        )
        topic_receipt = topic_tx.execute(client)
        topic_id = topic_receipt.topic_id
        print(f"✅ Success! Created topic: {topic_id}")

        return topic_id
    except Exception as e:
        print(f"❌ Error: Creating topic: {e}")
        sys.exit(1)


def submit_topic_message_transaction(client, topic_id, message, operator_key):
    """Submit a message to the specified topic."""
    print("\nSTEP 2: Submitting message...")
    transaction = (
        TopicMessageSubmitTransaction(topic_id=topic_id, message=message).freeze_with(client).sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(
            f"Message Submit Transaction completed: "
            f"(status: {ResponseCode(receipt.status).name}, "
            f"transaction_id: {receipt.transaction_id})"
        )
        print(f"✅ Success! Message submitted to topic {topic_id}: {message}")
    except Exception as e:
        print(f"❌ Error: Message submission failed: {str(e)}")
        sys.exit(1)


def main():
    """A example to create a topic and then submit a message to it."""
    message = "Hello, Hiero!"

    # Config Client
    client, _, operator_key = setup_client()

    # Create a new Topic
    topic_id = create_topic(client, operator_key)

    # Submit message to topic
    submit_topic_message_transaction(client, topic_id, message, operator_key)


if __name__ == "__main__":
    main()
