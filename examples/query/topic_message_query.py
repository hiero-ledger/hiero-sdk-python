"""
uv run examples/query/topic_message_query.py
python examples/query/topic_message_query.py

"""

import time
import sys
from datetime import datetime, timezone

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    TopicMessageQuery,
)


def setup_client():
    """Initialize and set up the client using env vars."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    
    # Return tuple to match what main() expects
    return client, client.operator_account_id, client.operator_private_key


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
        print(f"❌ Error: Creating topic: {e}")
        sys.exit(1)


def query_topic_messages():
    """
    A full example that creates a topic and perform query topic messages.
    """
    # Config Client
    client, _, operator_key = setup_client()

    # Create Topic
    topic_id = create_topic(client, operator_key)

    # Query Topic Messages
    print("\nSTEP 2: Query Topic Messages...")

    def on_message_handler(topic_message):
        print(f"Received topic message: {topic_message}")

    def on_error_handler(e):
        print(f"Subscription error: {e}")

    query = TopicMessageQuery(
        topic_id=topic_id,
        start_time=datetime.now(timezone.utc),
        limit=0,
        chunking_enabled=True,
    )

    handle = query.subscribe(
        client, on_message=on_message_handler, on_error=on_error_handler
    )

    print("Subscription started. Will auto-cancel after 10 seconds or on Ctrl+C...")
    try:
        startTime = time.time()
        while time.time() - startTime < 10:
            time.sleep(1)
    except KeyboardInterrupt:
        print("✋ Ctrl+C detected. Cancelling subscription...")
    finally:
        handle.cancel()
        print("✅ Subscription cancelled. Exiting.")


if __name__ == "__main__":
    query_topic_messages()
