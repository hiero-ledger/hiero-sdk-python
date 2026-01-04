"""
uv run examples/query/topic_info_query.py
python examples/query/topic_info_query.py

"""

import sys
from hiero_sdk_python import (
    Client,
    TopicInfoQuery,
    TopicCreateTransaction,
)


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


def query_topic_info():
    """
    A full example that create a topic and query topic info for that topic.
    """
    # Config Client
    client = Client.from_env()
    print(f"Operator: {client.operator_account_id}")

    # Create a new Topic
    topic_id = create_topic(client, client.operator_private_key)

    # Query Topic Info
    print("\nSTEP 2: Querying Topic Info...")
    query = TopicInfoQuery().set_topic_id(topic_id)
    topic_info = query.execute(client)
    print("✅ Success! Topic Info:", topic_info)


if __name__ == "__main__":
    query_topic_info()
