"""
Unit tests for FileContentsQuery.
"""

from unittest.mock import Mock

import pytest

from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    file_get_contents_pb2,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of FileContentsQuery."""
    file_id = FileId(0, 0, 2)

    query = FileContentsQuery()
    assert query.file_id is None

    query = FileContentsQuery(file_id)
    assert query.file_id == file_id


def test_execute_fails_with_missing_file_id(mock_client):
    """Test request creation with missing File ID."""
    query = FileContentsQuery()

    with pytest.raises(
        ValueError, match="File ID must be set before making the request."
    ):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = FileContentsQuery()

    mock_channel = Mock()
    mock_file_stub = Mock()
    mock_channel.file = mock_file_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_file_stub.getFileContent


def test_file_contents_query_execute():
    """Test basic functionality of FileContentsQuery with mock server."""
    file_id = FileId(0, 0, 2)
    test_contents = b"Test file contents"

    # Create file contents response with test data
    file_contents_response = file_get_contents_pb2.FileGetContentsResponse.FileContents(
        fileID=file_id._to_proto(), contents=test_contents
    )

    response_sequences = get_file_contents_responses(file_contents_response)

    with mock_hedera_servers(response_sequences) as client:
        query = FileContentsQuery(file_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert result == test_contents


def get_file_contents_responses(file_contents_response):
    """Get the responses for the file contents query."""
    return [
        [
            response_pb2.Response(
                fileGetContents=file_get_contents_pb2.FileGetContentsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                fileGetContents=file_get_contents_pb2.FileGetContentsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                fileGetContents=file_get_contents_pb2.FileGetContentsResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    fileContents=file_contents_response,
                )
            ),
        ]
    ]
