"""
uv run examples/consensus/topic_update_transaction.py
python examples/consensus/topic_update_transaction.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicUpdateTransaction,
    Network,
    TopicCreateTransaction,
    ResponseCode,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

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
