import pytest
from unittest.mock import Mock

from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2, 
    response_header_pb2,
    token_get_info_pb2,
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture token_id as parameter
def test_constructor(token_id):
    """Test initialization of TokenInfoQuery."""
    query = TokenInfoQuery()
    assert query.token_id is None
    
    query = TokenInfoQuery(token_id)
    assert query.token_id == token_id

# This test uses fixture mock_client as parameter
def test_execute_fails_with_missing_token_id(mock_client):
    """Test request creation with missing Token ID."""
    query = TokenInfoQuery()
    
    with pytest.raises(ValueError, match="Token ID must be set before making the request."):
        query.execute(mock_client)

def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = TokenInfoQuery()
    
    mock_channel = Mock()
    mock_token_stub = Mock()
    mock_channel.token = mock_token_stub
    
    method = query._get_method(mock_channel)
    
    assert method.transaction is None
    assert method.query == mock_token_stub.getTokenInfo

# This test uses fixture (mock_account_ids, private_key) as parameter
def test_token_info_query_execute(mock_account_ids, private_key):
    """Test basic functionality of TokenInfoQuery with mock server."""
    account_id, renew_account_id, _, token_id, _ = mock_account_ids
    token_info_response = token_get_info_pb2.TokenInfo(
        tokenId=token_id._to_proto(),
        name="Test Token",
        symbol="TEST",
        decimals=8,
        totalSupply=100,
        treasury=account_id._to_proto(),
        defaultFreezeStatus=0,
        defaultKycStatus=0,
        autoRenewAccount=renew_account_id._to_proto(),
        maxSupply=10000,
        adminKey=private_key.public_key()._to_proto(),
        kycKey=private_key.public_key()._to_proto(),
        wipeKey=private_key.public_key()._to_proto(),
    )

    responses = [
        response_pb2.Response(
            tokenGetInfo=token_get_info_pb2.TokenGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            tokenGetInfo=token_get_info_pb2.TokenGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            tokenGetInfo=token_get_info_pb2.TokenGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.ANSWER_ONLY,
                    cost=2
                ),
                tokenInfo=token_info_response
            )
        )
    ]
    
    response_sequences = [responses]
    
    with mock_hedera_servers(response_sequences) as client:
        query = TokenInfoQuery(token_id)
        
        try:
            # Get the cost of executing the query - should be 2 tinybars based on the mock response
            cost = query.get_cost(client)
            assert cost.to_tinybars() == 2
            
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        assert result.token_id == token_id
        assert result.name == "Test Token"
        assert result.symbol == "TEST"
        assert result.decimals == 8
        assert result.total_supply == 100
        assert result.max_supply == 10000
        assert result.treasury == account_id
        assert result.auto_renew_account == renew_account_id
        assert result.default_freeze_status == 0
        assert result.default_freeze_status == 0
        assert result.admin_key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.kyc_key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.wipe_key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.supply_key == None
        assert result.freeze_key == None