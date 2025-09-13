"""Create a new topic on Hedera"""

# Usage:
"""
uv run examples/topic_create.py
python examples/topic_create.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    Network,
)

load_dotenv()

def setup_client():
    """Setup and return a Hedera client."""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)
        
def create_topic():
    """ Create a new topic on Hedera """
    client, operator_id, operator_key = setup_client()
    print("\nCreating a new topic...")

    transaction = (
        TopicCreateTransaction(
            memo="Python SDK created topic",
            admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topic_id:
            print(f"Topic created with ID: {receipt.topic_id}")
        else:
            print("Topic creation failed: Topic ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_topic()
