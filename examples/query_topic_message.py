import os
import time
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    TopicMessageQuery
)

load_dotenv()

def query_topic_messages():
    """
    A full example that creates a topic and perform query topic messages.
    """
    # Config Client
    print("Connecting to Hedera testnet...")
    network = Network(network='testnet')
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

    # Create Topic
    print("\nCreating a Topic...")
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
    except Exception as e:
        print(f"❌ Error: Creating topic: {e}")
        sys.exit(1)

    # Query Topic Messages
    print("\nQuery Topic Messages...")
    def on_message_handler(topic_message):
        print(f"Received topic message: {topic_message}")

    def on_error_handler(e):
        print(f"Subscription error: {e}")

    query = TopicMessageQuery(
        topic_id=topic_id,
        start_time=datetime.now(timezone.utc),
        limit=0,
        chunking_enabled=True
    )

    handle = query.subscribe(
        client,
        on_message=on_message_handler,
        on_error=on_error_handler
    )

    print("Subscription started. Press Ctrl+C to cancel...")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Cancelling subscription...")
        handle.cancel()
        handle.join()
        print("Subscription cancelled. Exiting.")

if __name__ == "__main__":
    query_topic_messages()
