"""
uv run examples/consensus/topic_create_transaction.py
python examples/consensus/topic_create_transaction.py
"""
from hiero_sdk_python import Client, TopicCreateTransaction, ResponseCode, PrivateKey

def setup_client():
    """
    Sets up and configures the Hiero client.
    Reads OPERATOR_ID and OPERATOR_KEY from environment variables via Client.from_env().
    """
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client, client.operator_private_key

def create_topic(client: Client, operator_key: PrivateKey):
    """
    Builds, signs, and executes a new topic creation transaction.
    """
    transaction = (
        TopicCreateTransaction(
            memo="Python SDK created topic", admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )
    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Topic creation failed: {ResponseCode(receipt.status).name}")
            raise SystemExit(1)
        if not receipt.topic_id:
            print("Topic creation failed: Topic ID not returned in receipt.")
            raise SystemExit(1)
        print(f"Success! Topic created with ID: {receipt.topic_id}")
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")
        raise SystemExit(1)

def main():
    """
    Main workflow to set up the client and create a new topic.
    """
    client, operator_key = setup_client()
    create_topic(client, operator_key)

if __name__ == "__main__":
    main()