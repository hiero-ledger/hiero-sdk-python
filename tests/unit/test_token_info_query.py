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
def test_execute_without_token_id(mock_client):
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

# This test uses fixture mock_account_ids as parameter
def test_token_info_query_execute(mock_account_ids):
    """Test basic functionality of TokenInfoQuery with mock server."""
    account_id, renew_account_id, _, token_id, _ = mock_account_ids
    token_info_response = token_get_info_pb2.TokenInfo(
        tokenId=token_id.to_proto(),
        name="Test Token",
        symbol="TEST",
        decimals=8,
        totalSupply=1000000,
        treasury=account_id.to_proto(),
        adminKey=None,
        kycKey=None,
        freezeKey=None,
        wipeKey=None,
        supplyKey=None,
        defaultFreezeStatus=0,
        defaultKycStatus=0,
        deleted=False,
        autoRenewAccount=renew_account_id.to_proto(),
        autoRenewPeriod=None,
        expiry=None,
        memo="",
        tokenType=0,
        supplyType=0,
        maxSupply=0,
        fee_schedule_key=None,
        custom_fees=None,
        pause_key=None,
        pause_status=0,
        metadata_key=None,
        ledger_id=None
    )

    response = response_pb2.Response(
            tokenGetInfo=token_get_info_pb2.TokenGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.ANSWER_ONLY,
                    cost=2
                ),
                tokenInfo=token_info_response
            )
        )
    
    response_sequences = [[response]]
    
    with mock_hedera_servers(response_sequences) as client:
        query = TokenInfoQuery().set_token_id(token_id)
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
        # Verify the result contains the expected values
        assert result.tokenId.shard == 1
        assert result.tokenId.realm == 1
        assert result.tokenId.num == 1
        assert result.name == "Test Token"
        assert result.symbol == "TEST"
        assert result.decimals == 8
        assert result.totalSupply == 1000000
        assert result.treasury.shard == 0
        assert result.treasury.realm == 0
        assert result.treasury.num == 1
        assert result.autoRenewAccount.shard == 0
        assert result.autoRenewAccount.realm == 0
        assert result.autoRenewAccount.num == 2
        assert result.defaultFreezeStatus == 0
        assert result.defaultKycStatus == 0
        assert result.isDeleted == False