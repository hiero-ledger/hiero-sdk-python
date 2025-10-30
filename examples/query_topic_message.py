"""
uv run examples/query_topic_message.py 
python examples/query_topic_message.py

"""
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
network_name = os.getenv('NETWORK', 'testnet').lower()
def setup_client():
    """Initialize and set up the client with operator account"""
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))

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
        chunking_enabled=True
    )

    handle = query.subscribe(
        client,
        on_message=on_message_handler,
        on_error=on_error_handler
    )

    print("Subscription started. Will auto-cancel after 10 seconds or on Ctrl+C...")
    try:
        startTime = time.time();
        while time.time() - startTime < 10:
            time.sleep(1);
    except KeyboardInterrupt:
        print("✋ Ctrl+C detected. Cancelling subscription...")
    finally:
        handle.cancel()
        print("✅ Subscription cancelled. Exiting.")

if __name__ == "__main__":
    query_topic_messages()
