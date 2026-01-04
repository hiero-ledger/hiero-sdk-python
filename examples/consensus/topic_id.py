"""uv run examples/consensus/topic_id.py"""

from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network


def create_topic_id() -> TopicId:
    """Create a TopicId manually."""
    topic_id = TopicId(shard=0, realm=0, num=1234)

    print(f"  Shard: {topic_id.shard}")
    print(f"  Realm: {topic_id.realm}")
    print(f"  Num: {topic_id.num}")

    return topic_id


def parse_topic_id() -> TopicId:
    """Parse a TopicId from string representation."""
    topic_id_str = "0.0.1234"
    topic_id = TopicId.from_string(topic_id_str)

    print(f"  Shard: {topic_id.shard}")
    print(f"  Realm: {topic_id.realm}")
    print(f"  Num: {topic_id.num}")

    return topic_id


def convert_to_proto_and_back(topic_id: TopicId) -> TopicId:
    """Convert a TopicId to protobuf and back."""
    proto = topic_id._to_proto()
    topic_id = TopicId._from_proto(proto)

    print(f"  Shard: {topic_id.shard}")
    print(f"  Realm: {topic_id.realm}")
    print(f"  Num: {topic_id.num}")

    return topic_id


def show_with_checksum(client: Client, topic_id: TopicId):
    """Display TopicId with checksum."""
    topic_id_with_checksum = topic_id.to_string_with_checksum(client)

    print(f"  TopicId with checksum: {topic_id_with_checksum}")


def main():
    """Demonstrate TopicId functionality."""
    topic_id = TopicId(shard=0, realm=0, num=1234)
    network = Network("testnet")
    client = Client(network)

    # Create a TopicId
    create_topic_id()

    # Parse a TopicId from string representation
    parse_topic_id()

    # Convert a TopicId to protobuf and back
    convert_to_proto_and_back(topic_id)

    # Display TopicId with checksum
    show_with_checksum(client, topic_id)


if __name__ == "__main__":
    main()
