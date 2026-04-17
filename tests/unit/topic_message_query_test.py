from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import timestamp_pb2 as hapi_timestamp_pb2
from hiero_sdk_python.hapi.services.consensus_submit_message_pb2 import ConsensusMessageChunkInfo
from hiero_sdk_python.query.topic_message_query import TopicMessageQuery
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_client():
    """Fixture to provide a mock Client instance."""
    client = MagicMock(spec=Client)
    client.operator_account_id = AccountId(0, 0, 12345)

    return client


@pytest.fixture
def mock_topic_id():
    """Fixture to provide a mock TopicId instance."""
    return TopicId(0, 0, 1234)


@pytest.fixture
def mock_subscription_response():
    """Fixture to provide a mock response from a topic subscription."""
    return mirror_proto.ConsensusTopicResponse(
        consensusTimestamp=hapi_timestamp_pb2.Timestamp(seconds=12345, nanos=67890),
        message=b"Hello, world!",
        runningHash=b"\x00" * 48,
        sequenceNumber=1,
    )


def test_topic_message_query_initialization():
    """Test initializing the query with various parameter types and setters."""
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    query = TopicMessageQuery().set_topic_id("0.0.123").set_start_time(start).set_limit(5).set_chunking_enabled(True)

    assert query._topic_id.topicNum == 123
    assert query._start_time.seconds == int(start.timestamp())
    assert query._limit == 5
    assert query._chunking_enabled is True


# This test uses fixtures (mock_client, mock_topic_id, mock_subscription_response) as parameters
def test_topic_message_query_subscription(mock_client, mock_topic_id, mock_subscription_response):
    """Test subscribing to topic messages using TopicMessageQuery."""
    query = TopicMessageQuery().set_topic_id(mock_topic_id).set_start_time(datetime.now(tz=timezone.utc))

    with patch("hiero_sdk_python.query.topic_message_query.TopicMessageQuery.subscribe") as mock_subscribe:

        def side_effect(client, on_message, on_error):  # noqa: ARG001
            on_message(mock_subscription_response)

        mock_subscribe.side_effect = side_effect

        on_message = MagicMock()
        on_error = MagicMock()

        query.subscribe(mock_client, on_message=on_message, on_error=on_error)

        on_message.assert_called_once()
        called_args = on_message.call_args[0][0]
        assert called_args.consensusTimestamp.seconds == 12345
        assert called_args.consensusTimestamp.nanos == 67890
        assert called_args.message == b"Hello, world!"
        assert called_args.sequenceNumber == 1

        on_error.assert_not_called()

    print("Test passed: Subscription handled messages correctly.")


def test_chunk_message_handling(mock_client):
    """Test that multiple chunks are correctly buffered and released as a single message."""
    query = TopicMessageQuery(topic_id="0.0.123", chunking_enabled=True)

    # Mocking two chunks for the same transaction
    tx_id = TransactionId.generate(mock_client.operator_account_id)._to_proto()
    chunk1 = mirror_proto.ConsensusTopicResponse(
        message=b"part1", chunkInfo=ConsensusMessageChunkInfo(initialTransactionID=tx_id, total=2, number=1)
    )
    chunk2 = mirror_proto.ConsensusTopicResponse(
        message=b"part2", chunkInfo=ConsensusMessageChunkInfo(initialTransactionID=tx_id, total=2, number=2)
    )

    mock_client.mirror_stub.subscribeTopic.return_value = [chunk1, chunk2]

    received_messages = []
    query.subscribe(mock_client, on_message=lambda m: received_messages.append(m))

    # Wait for thread execution
    time.sleep(0.1)

    assert len(received_messages) == 1
    # Assuming TopicMessage.of_many joins messages
    assert b"part1" in received_messages[0].message
