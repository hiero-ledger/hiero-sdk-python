import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    TopicInfoQuery,
    TopicCreateTransaction
)

load_dotenv()

def query_topic_info():
    """
    A full example that create a topic and query topic info for that topic.
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

    # Create a new Topic
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

    # Query Topic Info
    print("\nQuerying Topic Info...")
    query = TopicInfoQuery().set_topic_id(topic_id)
    topic_info = query.execute(client)
    print("✅ Success! Topic Info:", topic_info)

if __name__ == "__main__":
    query_topic_info()
