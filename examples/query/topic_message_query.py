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
    ResponseCode,
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
    
    if operator_key is None:
        raise ValueError("Operator private key not set in environment")

    try:
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
    except Exception as e:
        print(f"Error creating topic: {e}")
        sys.exit(1)


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
        
        receipt = response.get_receipt(client)
        if receipt.status != ResponseCode.SUCCESS:
             print(f"Warning: Message submission status: {ResponseCode(receipt.status).name}")

        print(f"Submitted message: {message}")
        time.sleep(2)