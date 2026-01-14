"""
uv run examples/query/topic_message_query.py
python examples/query/topic_message_query.py
"""

import sys
import time
from datetime import datetime, timezone

from hiero_sdk_python import (
    Client,
    TopicCreateTransaction,
    TopicMessageQuery,
)


def create_topic(client):
    """Create a new topic"""
    print("\nSTEP 1: Creating a Topic...")

    operator_key = client.operator_private_key
    if operator_key is None:
        raise ValueError("Operator private key not set in environment")

    try:
        topic_tx = (
            TopicCreateTransaction(
                memo="Python SDK created topic",
                admin_key=operator_key.public_key(),
            )
            .freeze_with(client)
            .sign(operator_key)
        )

        receipt = topic_tx.execute(client)
        topic_id = receipt.topic_id

        print(f"Success! Created topic: {topic_id}")
        return topic_id

    except Exception as e:
        print(f"Error creating topic: {e}")
        sys.exit(1)


def query_topic_messages():
    """
    Creates a topic and queries topic messages.
    """
    # Configure client from environment
    client = Client.from_env()

    if client.operator_account_id is None:
        raise ValueError("OPERATOR_ID must be set in environment")

    print(f"Operator: {client.operator_account_id}")

    # Create Topic
    topic_id = create_topic(client)

    # Query Topic Messages
    print("\nSTEP 2: Query Topic Messages...")

    def on_message_handler(topic_message):
        print(f"Received topic message: {topic_message}")

    def on_error_handler(error):
        print(f"Subscription error: {error}")

    query = TopicMessageQuery(
        topic_id=topic_id,
        start_time=datetime.now(timezone.utc),
        limit=0,
        chunking_enabled=True,
    )

    handle = query.subscribe(
        client,
        on_message=on_message_handler,
        on_error=on_error_handler,
    )

    print("Subscription started. Will auto-cancel after 10 seconds or on Ctrl+C...")
    try:
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl+C detected. Cancelling subscription...")
    finally:
        handle.cancel()
        print("Subscription cancelled. Exiting.")


if __name__ == "__main__":
    query_topic_messages()
