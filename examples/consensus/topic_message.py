"""
This example should demonstrate:

1. How to manually create TopicMessageChunk objects with mock data.
2. How to build TopicMessage instances using of_single() and of_many() style
3. How to inspect key fields (consensus timestamp, contents, sequence number, transaction ID)
4. How to pretty-print a TopicMessage and iterate over chunks

To run : use
uv run examples/consensus/topic_message.py
python examples/consensus/topic_message.py

"""

from hiero_sdk_python.consensus.topic_message import TopicMessage, TopicMessageChunk


class MockTimestamp:
    """Mocks the protobuf Timestamp object."""

    def __init__(self, seconds: int, nanos: int = 0):
        self.seconds = seconds
        self.nanos = nanos


class MockAccountID:
    """Mocks the protobuf AccountID object."""

    def __init__(self, shard, realm, num):
        self.shardNum = shard
        self.realmNum = realm
        self.accountNum = num
        self.alias = None


class MockTransactionID:
    """Mocks the protobuf TransactionID object."""

    def __init__(self, account_id, seconds, nanos):

        self.accountID = account_id
        self.transactionValidStart = MockTimestamp(seconds, nanos)
        self.scheduled = False


class MockChunkInfo:
    """Mocks the protobuf ChunkInfo object."""

    def __init__(self, seq: int, total_chunks: int, tx_id: MockTransactionID = None):
        self.number = seq
        self.total = total_chunks
        self.initialTransactionID = tx_id

    def HasField(self, field_name: str) -> bool:
        """Simulates the protobuf HasField method."""
        if field_name == "initialTransactionID":
            return self.initialTransactionID is not None
        return False


class MockResponse:
    """Mocks the protobuf ConsensusTopicResponse object."""

    def __init__(
        self,
        message: bytes,
        seq: int,
        timestamp: MockTimestamp,
        chunk_info: MockChunkInfo = None,
    ):
        self.message = message
        self.runningHash = b"mock_running_hash_" + str(seq).encode()
        self.sequenceNumber = seq
        self.consensusTimestamp = timestamp
        self.chunkInfo = chunk_info

    def HasField(self, field_name: str) -> bool:
        """Simulates the protobuf HasField method."""
        if field_name == "chunkInfo":
            return self.chunkInfo is not None
        return False


def mock_consensus_response(
    message: bytes,
    seq: int = 1,
    is_chunked: bool = False,
    total_chunks: int = 1,
    has_tx_id: bool = False,
) -> MockResponse:
    """
    Creates a lightweight mock of a ConsensusTopicResponse
    that satisfies the interface required by TopicMessage.
    """
    timestamp = MockTimestamp(1736539200 + seq, 123456000 + seq)

    chunk_info = None
    if is_chunked:
        tx_id = (
            MockTransactionID(MockAccountID(0, 0, 10), 1736539100, 1)
            if has_tx_id
            else None
        )
        chunk_info = MockChunkInfo(seq, total_chunks, tx_id)

    return MockResponse(message, seq, timestamp, chunk_info)


def demonstrate_single_chunk():
    """Demonstrate TopicMessage with a single, un-chunked message."""
    print("--- 1. Single-Chunk TopicMessage ---")

    response = mock_consensus_response(b"Hello from a single chunk!", seq=1)

    topic_msg = TopicMessage.of_single(response)

    print(f"Pretty-print: {topic_msg}")

    print(f"  Contents: {topic_msg.contents.decode('utf-8')}")
    print(f"  Sequence No: {topic_msg.sequence_number}")
    print(f"  Timestamp: {topic_msg.consensus_timestamp}")
    print(f"  Chunks: {len(topic_msg.chunks)}")


def demonstrate_multi_chunk():
    """Demonstrate TopicMessage by reassembling multiple chunks."""
    print("\n--- 2. Multi-Chunk TopicMessage ---")

    responses = [
        mock_consensus_response(
            b"This is the first part, ", seq=1, is_chunked=True, total_chunks=3
        ),
        mock_consensus_response(
            b"this is the second, ", seq=2, is_chunked=True, total_chunks=3
        ),
        mock_consensus_response(
            b"and this is the end.", seq=3, is_chunked=True, total_chunks=3
        ),
    ]

    topic_msg = TopicMessage.of_many(responses)

    print(f"Pretty-print: {topic_msg}")

    print(f"  Reassembled Contents: {topic_msg.contents.decode('utf-8')}")
    print(f"  Final Sequence No: {topic_msg.sequence_number}")
    print(f"  Final Timestamp: {topic_msg.consensus_timestamp}")
    print(f"  Total Chunks: {len(topic_msg.chunks)}")

    print("  Inspecting individual chunks:")
    for chunk in topic_msg.chunks:
        print(
            f"    - Chunk Seq: {chunk.sequence_number}, Size: {chunk.content_size} bytes"
        )


def demonstrate_transaction_id():
    """Demonstrate extracting the Transaction ID from a chunk."""
    print("\n--- 3. TopicMessage with Transaction ID ---")

    response = mock_consensus_response(
        b"This message has a TX ID",
        seq=1,
        is_chunked=True,
        total_chunks=1,
        has_tx_id=True,
    )

    topic_msg = TopicMessage.of_single(response)

    print(f"Pretty-print: {topic_msg}")

    print(f"  Extracted Transaction ID: {topic_msg.transaction_id}")


def main():
    """
    Runs all demonstrations for TopicMessage and TopicMessageChunk.
    This example is self-contained and does not connect to the network.
    """
    print("Running TopicMessage examples...")

    demonstrate_single_chunk()
    demonstrate_multi_chunk()
    demonstrate_transaction_id()


if __name__ == "__main__":
    main()
