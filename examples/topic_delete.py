import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicId,
    TopicDeleteTransaction,
    Network,
)

load_dotenv()

def delete_topic():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    topic_id = TopicId.from_string(os.getenv('TOPIC_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TopicDeleteTransaction(topic_id=topic_id)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(f"Topic {topic_id} deleted successfully.")
    except Exception as e:
        print(f"Topic deletion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    delete_topic()
