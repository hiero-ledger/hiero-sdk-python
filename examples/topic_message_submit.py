"""
uv run examples/topic_message_submit.py
python examples/topic_message_submit.py

"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TopicMessageSubmitTransaction,
    TopicCreateTransaction,
    ResponseCode
)

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

def create_topic(client, operator_key):
    """Create a new topic"""
    print("\nSTEP 1: Creating a Topic...")
    try:
        topic_tx = (
            TopicCreateTransaction(
                memo="Python SDK created topic",
                admin_key=operator_key.public_key()
            )
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


def submit_message(message):
    """
    A example to create a topic and then submit a message to it.
    """
    # Config Client
    client, _, operator_key = setup_client()

    # Create a new Topic
    topic_id = create_topic(client, operator_key)

    # Submit message to topic
    print("\nSTEP 2: Submitting message...")
    transaction = (
        TopicMessageSubmitTransaction(topic_id=topic_id, message=message)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(f"Message Submit Transaction completed: "
              f"(status: {ResponseCode(receipt.status).name}, "
              f"transaction_id: {receipt.transaction_id})")
        print(f"✅ Success! Message submitted to topic {topic_id}: {message}")
    except Exception as e:
        print(f"❌ Error: Message submission failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    submit_message("Hello, Hiero!")
