import os
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    TopicId,
    TopicInfoQuery,
)

load_dotenv()

def query_topic_info():
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    topic_id = TopicId.from_string(os.getenv('TOPIC_ID'))

    network = Network(network='testnet')
    client = Client(network)
    client.set_operator(operator_id, operator_key)

    query = TopicInfoQuery().set_topic_id(topic_id)
    topic_info = query.execute(client)
    print("Topic Info:", topic_info)

if __name__ == "__main__":
    query_topic_info()
