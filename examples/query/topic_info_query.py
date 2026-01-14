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


def query_topic_info():
    """
    Creates a topic and queries topic information.
    """
    client = Client.from_env()

    if client.operator_account_id is None:
        raise ValueError("OPERATOR_ID must be set in environment")

    print(f"Operator: {client.operator_account_id}")

    topic_id = create_topic(client)

    print("\nSTEP 2: Querying Topic Info...")
    info = TopicInfoQuery().set_topic_id(topic_id).execute(client)

    print("Success! Topic Info:")
    print(info)


if __name__ == "__main__":
    query_topic_info()
