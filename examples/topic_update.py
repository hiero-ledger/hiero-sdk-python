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
    ResponseCode
)

load_dotenv()

def update_topic(new_memo):
    """
    A example to create a topic and then update it.
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

    # Update the Topic
    print("\nUpdating Topic...")
    transaction = (
        TopicUpdateTransaction(topic_id=topic_id, memo=new_memo)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(f"Topic Update Transaction completed: "
              f"(status: {ResponseCode(receipt.status).name}, "
              f"transaction_id: {receipt.transaction_id})")
        print(f"✅ Success! Topic {topic_id} updated with new memo: {new_memo}")
    except Exception as e:
        print(f"❌ Error: Topic update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_topic("Updated topic memo")
