from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import grpc
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import timestamp_pb2 as hapi_timestamp_pb2
from hiero_sdk_python.hapi.services.consensus_submit_message_pb2 import ConsensusMessageChunkInfo
from hiero_sdk_python.query.topic_message_query import TopicMessageQuery
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import RealRpcError


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_client():
    """Fixture to provide a mock Client instance."""
    client = MagicMock(spec=Client)
    client.operator_account_id = AccountId(0, 0, 12345)
    client.mirror_stub = MagicMock()

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
        message=b"Hello Hiero!",
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


def test_topic_message_query_invalid_max_backoff():
    """Test that invalid max_backoff raises errors."""
    query = TopicMessageQuery()

    with pytest.raises(ValueError, match="max_backoff must be at least 500 ms"):
        query.set_max_backoff(0.1)


def test_topic_message_query_invalid_max_attempts():
    """Test that invalid max_attempts raises errors."""
    query = TopicMessageQuery()

    with pytest.raises(ValueError, match="max_attempts must be greater than 0"):
        query.set_max_attempts(0)


def test_topic_message_query_invalid_topic_id():
    """Test that invalid topic_id raises errors."""
    query = TopicMessageQuery()

    # Invalid TopicId type
    with pytest.raises(TypeError, match="Invalid topic_id format"):
        query.set_topic_id(12345)

    # Invalid TopicId format
    with pytest.raises(ValueError, match="Invalid topic ID string"):
        query.set_topic_id("12345")


def test_subscribe_missing_config(mock_client):
    """Test that subscribe fails if Topic ID or Mirror Stub is missing."""
    # No TopicId
    query_no_id = TopicMessageQuery()
    with pytest.raises(ValueError, match="Topic ID must be set before subscribing"):
        query_no_id.subscribe(mock_client, on_message=MagicMock())

    # No MirrorStub
    query_ok = TopicMessageQuery(topic_id="0.0.123")
    mock_client.mirror_stub = None
    with pytest.raises(ValueError, match="Client has no mirror_stub"):
        query_ok.subscribe(mock_client, on_message=MagicMock())


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
        assert called_args.message == b"Hello Hiero!"
        assert called_args.sequenceNumber == 1

        on_error.assert_not_called()


def test_chunk_message_handling_improved(mock_client):
    """Test that multiple chunks are correctly buffered and released as a single message."""
    query = TopicMessageQuery(topic_id="0.0.123", chunking_enabled=True)

    tx_id = TransactionId.generate(mock_client.operator_account_id)
    tx_id_proto = tx_id._to_proto()

    chunk1 = mirror_proto.ConsensusTopicResponse(
        message=b"chunk-1", chunkInfo=ConsensusMessageChunkInfo(initialTransactionID=tx_id_proto, total=2, number=1)
    )
    chunk2 = mirror_proto.ConsensusTopicResponse(
        message=b"chunk-2", chunkInfo=ConsensusMessageChunkInfo(initialTransactionID=tx_id_proto, total=2, number=2)
    )

    mock_client.mirror_stub.subscribeTopic.return_value = iter([chunk1, chunk2])

    received_messages = []
    handle = query.subscribe(mock_client, on_message=lambda m: received_messages.append(m))

    handle._thread.join(timeout=1.0)

    assert len(received_messages) == 1
    assert b"chunk-1" in received_messages[0].contents
    assert b"chunk-2" in received_messages[0].contents


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.NOT_FOUND, "unavailable"),
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
        RealRpcError(grpc.StatusCode.INTERNAL, "received rst stream"),  # internal with rst stream
        Exception("non grpc exception"),  # non grpc exception
    ],
)
def test_retry_logic_on_retryable_error(mock_client, error):
    """Test that the query retries on retryable errors but stops after max_attempts."""
    query = TopicMessageQuery(topic_id="0.0.123").set_max_attempts(2).set_max_backoff(0.5)

    mock_client.mirror_stub.subscribeTopic.side_effect = [error, error]

    handle = query.subscribe(mock_client, on_message=MagicMock(), on_error=MagicMock())

    handle._thread.join(timeout=2.0)

    assert mock_client.mirror_stub.subscribeTopic.call_count == 2


@pytest.mark.parametrize(
    "non_retryable_error",
    [
        RealRpcError(grpc.StatusCode.PERMISSION_DENIED, "permission denied"),
        RealRpcError(grpc.StatusCode.INVALID_ARGUMENT, "invalid argument"),
        RealRpcError(grpc.StatusCode.UNAUTHENTICATED, "unauthenticated"),
        RealRpcError(grpc.StatusCode.INTERNAL, "internal error"),
    ],
)
def test_retry_logic_on_non_retryable_error(mock_client, non_retryable_error):
    """Test that the query stops immediately on non-transient errors."""
    query = TopicMessageQuery(topic_id="0.0.123").set_max_attempts(5).set_max_backoff(0.5)

    mock_client.mirror_stub.subscribeTopic.side_effect = [non_retryable_error] * 5

    on_error = MagicMock()
    handle = query.subscribe(mock_client, on_message=MagicMock(), on_error=on_error)

    handle._thread.join(timeout=1.0)

    assert mock_client.mirror_stub.subscribeTopic.call_count == 1
    on_error.assert_called_once_with(non_retryable_error)

    assert not handle._thread.is_alive()


def test_subscription_cancellation(mock_client):
    """Test that cancelling a handle stops the subscription thread."""
    query = TopicMessageQuery(topic_id="0.0.123")

    def infinite_stream():
        while True:
            yield mirror_proto.ConsensusTopicResponse(message=b"ping")
            time.sleep(0.1)

    mock_call = MagicMock()
    mock_call.__iter__.return_value = infinite_stream()

    mock_client.mirror_stub.subscribeTopic.return_value = mock_call

    on_message = MagicMock()
    handle = query.subscribe(mock_client, on_message=on_message)

    time.sleep(0.2)
    assert handle._thread.is_alive()

    handle.cancel()

    handle._thread.join(timeout=1.0)

    assert not handle._thread.is_alive()
    mock_call.cancel.assert_called()
