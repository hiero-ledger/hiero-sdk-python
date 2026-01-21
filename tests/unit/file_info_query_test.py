import pytest
from unittest.mock import Mock

from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2,
    response_header_pb2,
    file_get_info_pb2
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.timestamp import Timestamp

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_constructor():
    """Test initialization of FileInfoQuery."""
    file_id = FileId(0, 0, 2)
    
    query = FileInfoQuery()
    assert query.file_id is None
    
    query = FileInfoQuery(file_id)
    assert query.file_id == file_id

def test_execute_fails_with_missing_file_id(mock_client):
    """Test request creation with missing File ID."""
    query = FileInfoQuery()
    
    with pytest.raises(ValueError, match="File ID must be set before making the request."):
        query.execute(mock_client)

def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = FileInfoQuery()
    
    mock_channel = Mock()
    mock_file_stub = Mock()
    mock_channel.file = mock_file_stub
    
    method = query._get_method(mock_channel)
    
    assert method.transaction is None
    assert method.query == mock_file_stub.getFileInfo

def test_file_info_query_execute(private_key):
    """Test basic functionality of FileInfoQuery with mock server."""
    file_id = FileId(0, 0, 2)
    expiration_time = TimestampProto(seconds=1718745600)
    
    # Create file info response with test data
    file_info_response = file_get_info_pb2.FileGetInfoResponse.FileInfo(
        fileID=file_id._to_proto(),
        size=1000,
        expirationTime=expiration_time,
        deleted=False,
        keys=KeyListProto(keys=[private_key.public_key()._to_proto()]),
        memo="test memo"
    )

    response_sequences = get_file_info_responses(file_info_response)
    
    with mock_hedera_servers(response_sequences) as client:
        query = FileInfoQuery(file_id)
        
        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2
        
        # Execute query and get result
        result = query.execute(client)
        
        assert result.file_id == file_id
        assert result.size == 1000
        assert result.expiration_time == Timestamp._from_protobuf(expiration_time)
        assert not result.is_deleted
        assert result.keys[0].to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.file_memo == "test memo"

def get_file_info_responses(file_info_response):
    return [[
        response_pb2.Response(
            fileGetInfo=file_get_info_pb2.FileGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            fileGetInfo=file_get_info_pb2.FileGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            fileGetInfo=file_get_info_pb2.FileGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.ANSWER_ONLY,
                    cost=2
                ),
                fileInfo=file_info_response
            )
        )
    ]]
