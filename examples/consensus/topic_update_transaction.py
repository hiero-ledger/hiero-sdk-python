"""
uv run examples/consensus/topic_update_transaction.py
python examples/consensus/topic_update_transaction.py

"""

import sys

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicUpdateTransaction,
    Network,
    TopicCreateTransaction,
    ResponseCode,
)

def setup_client():
    """Initialize and set up the client using env vars."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
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

def update_topic(new_memo):
    """A example to create a topic and then update it"""
    # Config Client
    client, _, operator_key = setup_client()

    # Create Topic
    topic_id = create_topic(client, operator_key)

    # Update the Topic
    print("\nSTEP 2: Updating Topic...")
    transaction = (
        TopicUpdateTransaction(topic_id=topic_id, memo=new_memo)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(
            f"Topic Update Transaction completed: "
            f"(status: {ResponseCode(receipt.status).name}, "
            f"transaction_id: {receipt.transaction_id})"
        )
        print(f"✅ Success! Topic {topic_id} updated with new memo: {new_memo}")
    except Exception as e:
        print(f"❌ Topic update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_topic("Updated topic memo")
