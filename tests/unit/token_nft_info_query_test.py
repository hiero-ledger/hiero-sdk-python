import pytest
from unittest.mock import Mock

from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2, 
    response_header_pb2,
    timestamp_pb2, 
    token_get_nft_info_pb2,
    basic_types_pb2
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture nft_id as parameter
def test_constructor(nft_id):
    """Test initialization of TokenNftInfoQuery."""
    query = TokenNftInfoQuery()
    assert query.nft_id is None
    
    query = TokenNftInfoQuery(nft_id)
    assert query.nft_id == nft_id

# This test uses fixture mock_client as parameter
def test_execute_without_nft_id(mock_client):
    """Test request creation with missing NFT ID."""
    query = TokenNftInfoQuery()
    
    with pytest.raises(ValueError, match="NFT ID must be set before making the request."):
        query.execute(mock_client)

def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = TokenNftInfoQuery()
    
    mock_channel = Mock()
    mock_token_stub = Mock()
    mock_channel.token = mock_token_stub
    
    method = query._get_method(mock_channel)
    
    assert method.transaction is None
    assert method.query == mock_token_stub.getTokenNftInfo

# This test uses fixture nft_id as parameter
def test_execute_token_nft_info_query(nft_id):
    """Test basic functionality of TokenNftInfoQuery with mock server."""
    nft_info_response = token_get_nft_info_pb2.TokenNftInfo(
        nftID=basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(
                shardNum=0,
                realmNum=0,
                tokenNum=1
            ),
            serial_number=2
        ),
        accountID=basic_types_pb2.AccountID(
            shardNum=0,
            realmNum=0,
            accountNum=3
        ),
        creationTime=timestamp_pb2.Timestamp(seconds=1623456789),
        metadata=b'metadata'
    )
    responses = [
        response_pb2.Response(
            tokenGetNftInfo=token_get_nft_info_pb2.TokenGetNftInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            tokenGetNftInfo=token_get_nft_info_pb2.TokenGetNftInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            tokenGetNftInfo=token_get_nft_info_pb2.TokenGetNftInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.ANSWER_ONLY,
                    cost=2
                ),
                nft=nft_info_response
            )
        )
    ]
    
    response_sequences = [responses]
    
    with mock_hedera_servers(response_sequences) as client:
        query = TokenNftInfoQuery().set_nft_id(nft_id)
        
        try:
            # Get the cost of executing the query - should be 2 tinybars based on the mock response
            cost = query.get_cost(client)
            assert cost.to_tinybars() == 2
            
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        # Verify the result contains the expected values
        assert result.nft_id.token_id.shard == 0
        assert result.nft_id.token_id.realm == 0
        assert result.nft_id.token_id.num == 1
        assert result.nft_id.serial_number == 2
        assert result.account_id.shard == 0
        assert result.account_id.realm == 0
        assert result.account_id.num == 3
        assert result.metadata == b'metadata'