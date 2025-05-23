import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from hiero_sdk_python.query.topic_message_query import TopicMessageQuery
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from google.protobuf.timestamp_pb2 import Timestamp
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import timestamp_pb2 as hapi_timestamp_pb2

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_client():
    """Fixture to provide a mock Client instance."""
    client = MagicMock(spec=Client)
    client.operator_account_id = "0.0.12345"
    return client


@pytest.fixture
def mock_topic_id():
    """Fixture to provide a mock TopicId instance."""
    return TopicId(0, 0, 1234)

@pytest.fixture
def mock_subscription_response():
    """Fixture to provide a mock response from a topic subscription."""
    response = mirror_proto.ConsensusTopicResponse(
        consensusTimestamp=hapi_timestamp_pb2.Timestamp(seconds=12345, nanos=67890),
        message=b"Hello, world!",
        runningHash=b"\x00" * 48,
        sequenceNumber=1,
    )
    return response

# This test uses fixtures (mock_client, mock_topic_id, mock_subscription_response) as parameters
def test_topic_message_query_subscription(mock_client, mock_topic_id, mock_subscription_response):
    """
    Test subscribing to topic messages using TopicMessageQuery.
    """
    query = TopicMessageQuery().set_topic_id(mock_topic_id).set_start_time(datetime.now(timezone.utc))

    with patch("hiero_sdk_python.query.topic_message_query.TopicMessageQuery.subscribe") as mock_subscribe:
        def side_effect(client, on_message, on_error):
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
