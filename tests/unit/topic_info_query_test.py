"""Tests for the TopicInfoQuery functionality."""

import pytest

from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.executable import _ExecutionState
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    consensus_get_topic_info_pb2,
    consensus_topic_info_pb2,
    response_header_pb2,
    response_pb2,
    query_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def create_topic_info_response(status_code=ResponseCode.OK, with_info=True):
    """Helper function to create a topic info response with the given status."""
    topic_info = consensus_topic_info_pb2.ConsensusTopicInfo(
        memo="Test topic",
        runningHash=b"\x00" * 48,
        sequenceNumber=10,
        adminKey=basic_types_pb2.Key(ed25519=b"\x01" * 32)
    ) if with_info else consensus_topic_info_pb2.ConsensusTopicInfo()

    responses = [
        response_pb2.Response(
            consensusGetTopicInfo=consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            consensusGetTopicInfo=consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            consensusGetTopicInfo=consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=status_code
                ),
                topicInfo=topic_info
            )
        )
    ]
    
    return responses


def _response_with_status(status: ResponseCode) -> response_pb2.Response:
    """Create a Response with only the consensusGetTopicInfo header status set."""
    return response_pb2.Response(
        consensusGetTopicInfo=consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=status)
        )
    )


def test_topic_info_query(topic_id):
    """Test basic functionality of TopicInfoQuery with mock server."""
    responses = create_topic_info_response()
    response_sequences = [responses]
    
    with mock_hedera_servers(response_sequences) as client:
        query = (
            TopicInfoQuery()
            .set_topic_id(topic_id)
        )
        
        try:
            # Get the cost of executing the query - should be 2 tinybars based on the mock response
            cost = query.get_cost(client)
            assert cost.to_tinybars() == 2
            
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        # Verify the result contains the expected values
        assert isinstance(result, TopicInfo)
        assert result.memo == "Test topic"
        assert result.running_hash == b"\x00" * 48
        assert result.sequence_number == 10
        assert result.admin_key is not None


def test_topic_info_query_with_empty_topic_id():
    """Test that TopicInfoQuery validates topic_id before execution."""
    with mock_hedera_servers([[None]]) as client:
        query = TopicInfoQuery()  # No topic ID set
        
        with pytest.raises(ValueError) as exc_info:
            query.execute(client)
        
        assert "Topic ID must be set" in str(exc_info.value)


def test_make_request_builds_expected_protobuf(topic_id):
    """
    Covers TopicInfoQuery._make_request() using REAL protobuf classes.
    This is fast and deterministic (no network).
    """
    query = TopicInfoQuery().set_topic_id(topic_id)

    req = query._make_request()
    assert isinstance(req, query_pb2.Query)

    # Ensure the correct oneof field is populated
    assert req.HasField("consensusGetTopicInfo")
    assert req.consensusGetTopicInfo.HasField("topicID")

    # Compare serialized protobuf to avoid equality quirks
    expected_topic_id_proto = topic_id._to_proto()
    assert (
        req.consensusGetTopicInfo.topicID.SerializeToString()
        == expected_topic_id_proto.SerializeToString()
    )


def test_get_query_response_extracts_consensus_field():
    """Covers TopicInfoQuery._get_query_response()."""
    query = TopicInfoQuery()
    response = _response_with_status(ResponseCode.OK)

    out = query._get_query_response(response)
    assert out is response.consensusGetTopicInfo


@pytest.mark.parametrize(
    "status,expected_state",
    [
        (ResponseCode.OK, _ExecutionState.FINISHED),
        (ResponseCode.UNKNOWN, _ExecutionState.RETRY),
        (ResponseCode.BUSY, _ExecutionState.RETRY),
        (ResponseCode.PLATFORM_NOT_ACTIVE, _ExecutionState.RETRY),
        (ResponseCode.INVALID_TOPIC_ID, _ExecutionState.ERROR),
    ],
)
def test_should_retry_branches(status, expected_state):
    """Covers OK / RETRY / ERROR branches of TopicInfoQuery._should_retry()."""
    query = TopicInfoQuery()
    response = _response_with_status(status)

    assert query._should_retry(response) == expected_state


def test_freeze_prevents_set_topic_id_if_available(topic_id):
    """
    If TopicInfoQuery implements freeze semantics, ensure it prevents mutation.
    This is written to not break the suite if freeze() doesn't exist in your version.
    """
    query = TopicInfoQuery()

    if not hasattr(query, "freeze"):
        pytest.skip("TopicInfoQuery.freeze() not available in this SDK version")

    query.freeze()

    with pytest.raises(ValueError) as exc_info:
        query.set_topic_id(topic_id)

    assert "frozen" in str(exc_info.value).lower()
