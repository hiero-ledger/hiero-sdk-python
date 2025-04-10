"""Tests for the TopicInfoQuery functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    consensus_get_topic_info_pb2,
    consensus_topic_info_pb2,
    response_header_pb2,
    response_pb2
)
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode

from tests.mock_test import mock_hedera_servers

def create_topic_info_response(status_code=ResponseCode.OK, with_info=True):
    """Helper function to create a topic info response with the given status."""
    topic_info = consensus_topic_info_pb2.ConsensusTopicInfo(
        memo="Test topic",
        runningHash=b"\x00" * 48,
        sequenceNumber=10,
        adminKey=basic_types_pb2.Key(ed25519=b"\x01" * 32)
    ) if with_info else consensus_topic_info_pb2.ConsensusTopicInfo()
    
    response = response_pb2.Response(
        consensusGetTopicInfo=consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=status_code
            ),
            topicInfo=topic_info
        )
    )
    return response


def test_topic_info_query(topic_id):
    """Test basic functionality of TopicInfoQuery with mock server."""
    response = create_topic_info_response()
    response_sequences = [[response]]
    
    with mock_hedera_servers(response_sequences) as client:
        query = (
            TopicInfoQuery()
            .set_topic_id(topic_id)
        )
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        # Verify the result contains the expected values
        assert isinstance(result, TopicInfo)
        assert result.memo == "Test topic"
        assert result.running_hash == b"\x00" * 48
        assert result.sequence_number == 10
        assert result.admin_key is not None


def test_topic_info_query_retry_on_busy(topic_id):
    """Test that TopicInfoQuery retries on BUSY response."""
    # First response is BUSY, second is OK
    busy_response = create_topic_info_response(status_code=ResponseCode.BUSY, with_info=False)
    ok_response = create_topic_info_response()
    
    response_sequences = [[busy_response, ok_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        query = (
            TopicInfoQuery()
            .set_topic_id(topic_id)
        )
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify query was successful after retry
        assert result.memo == "Test topic"
        assert result.sequence_number == 10
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"
        
        # Verify we didn't switch nodes (BUSY is retriable without node switch)
        assert client.node_account_id == AccountId(0, 0, 3), "Should not have switched nodes on BUSY"


def test_topic_info_query_fails_on_nonretriable_error(topic_id):
    """Test that TopicInfoQuery fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = create_topic_info_response(status_code=ResponseCode.INVALID_TOPIC_ID, with_info=False)
    
    response_sequences = [[error_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        query = (
            TopicInfoQuery()
            .set_topic_id(topic_id)
        )
        
        # Verify query fails with the expected error
        with pytest.raises(PrecheckError) as exc_info:
            query.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.INVALID_TOPIC_ID) in str(exc_info.value)


def test_topic_info_query_with_empty_topic_id():
    """Test that TopicInfoQuery validates topic_id before execution."""
    with mock_hedera_servers([[None]]) as client:
        query = TopicInfoQuery()  # No topic ID set
        
        with pytest.raises(ValueError) as exc_info:
            query.execute(client)
        
        assert "Topic ID must be set" in str(exc_info.value)
