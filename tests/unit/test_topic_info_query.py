"""Tests for the TopicInfoQuery functionality."""

import pytest

from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    consensus_get_topic_info_pb2,
    consensus_topic_info_pb2,
    response_header_pb2,
    response_pb2
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
