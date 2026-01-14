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
    TopicMessageSubmitTransaction,
)


def setup_client():
    """Initialize and set up the client with operator account using env vars."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_topic(client):
    """Create a new topic"""
    print("Creating new topic...")
    operator_key = client.operator_private_key
    
    # FIX: Added null check
    if operator_key is None:
        raise ValueError("Operator private key not set in environment")

    transaction = (
        TopicCreateTransaction()
        .set_admin_key(operator_key.public_key())
        .set_submit_key(operator_key.public_key())
        .freeze_with(client)
        .sign(operator_key)
    )
    
    response = transaction.execute(client)
    topic_id = response.get_receipt(client).topic_id
    print(f"Topic created with ID: {topic_id}")
    return topic_id


def submit_messages(client, topic_id):
    """Submit messages to the topic"""
    print("Submitting messages...")
    for i in range(3):
        message = f"Hello Hiero! Message {i+1}"
        response = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message(message)
            .execute(client)
        )
        # FIX: Check receipt
        receipt = response.get_receipt(client)
        if receipt.status != 22: # SUCCESS
             print(f"Warning: Message submission status: {receipt.status}")

        print(f"Submitted message: {message}")
        time.sleep(2)


def main():
    client = setup_client()
    
    # Create a topic
    topic_id = create_topic(client)
    
    print("Subscribing to topic...")
    
    # Define the message handler
    def on_message_handler(message):
        print(f"Received message: {message.contents.decode('utf-8')} "
              f"at {message.consensus_timestamp}")

    # Define the error handler
    def on_error_handler(error):
        print(f"Error in subscription: {error}")

    # Create the query with no limit
    query = TopicMessageQuery(
        topic_id=topic_id,
        start_time=datetime.now(timezone.utc),
        limit=None,
        chunking_enabled=True,
    )

    # Subscribe to the topic
    # FIX: Changed on_next to on_message
    handle = query.subscribe(
        client, 
        on_message=on_message_handler,
        on_error=on_error_handler
    )

    # Submit some messages
    submit_messages(client, topic_id)

    # Keep the script running to receive messages
    print("Waiting for messages... (will exit in 10 seconds)")
    try:
        time.sleep(10)
    finally:
        print("Unsubscribing...")
        handle.cancel()


if __name__ == "__main__":
    main()