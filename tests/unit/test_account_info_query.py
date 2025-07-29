import pytest
from unittest.mock import Mock

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    response_pb2,
    response_header_pb2, 
    crypto_get_info_pb2
)
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.hapi.services.duration_pb2 import Duration as DurationProto
from hiero_sdk_python.timestamp import Timestamp

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_constructor():
    """Test initialization of AccountInfoQuery."""
    account_id = AccountId(0, 0, 2)
    
    query = AccountInfoQuery()
    assert query.account_id is None
    
    query = AccountInfoQuery(account_id)
    assert query.account_id == account_id

def test_execute_fails_with_missing_account_id(mock_client):
    """Test request creation with missing Account ID."""
    query = AccountInfoQuery()
    
    with pytest.raises(ValueError, match="Account ID must be set before making the request."):
        query.execute(mock_client)

def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = AccountInfoQuery()
    
    mock_channel = Mock()
    mock_crypto_stub = Mock()
    mock_channel.crypto = mock_crypto_stub
    
    method = query._get_method(mock_channel)
    
    assert method.transaction is None
    assert method.query == mock_crypto_stub.getAccountInfo

def test_account_info_query_execute(mock_account_ids, private_key):
    """Test basic functionality of AccountInfoQuery with mock server."""
    account_id = mock_account_ids[0]
    expiration_time = TimestampProto(seconds=1718745600)
    # 90 days in seconds
    auto_renew_period = DurationProto(seconds=7890000)
    
    # Create account info response with test data
    account_info_response = crypto_get_info_pb2.CryptoGetInfoResponse.AccountInfo(
        accountID=account_id._to_proto(),
        contractAccountID="",
        deleted=False,
        proxyReceived=0,
        key=private_key.public_key()._to_proto(),
        balance=1000,
        receiverSigRequired=False,
        expirationTime=expiration_time,
        autoRenewPeriod=auto_renew_period,
        memo="test memo",
        ownedNfts=0
    )

    response_sequences = get_account_info_responses(account_info_response)
    
    with mock_hedera_servers(response_sequences) as client:
        query = AccountInfoQuery(account_id)
        
        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2
        
        # Execute query and get result
        result = query.execute(client)
        
        assert result.account_id == account_id
        assert result.contract_account_id == ""
        assert not result.is_deleted
        assert result.proxy_received.to_tinybars() == 0
        assert result.key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        assert result.balance.to_tinybars() == 1000
        assert result.expiration_time == Timestamp._from_protobuf(expiration_time)
        assert result.auto_renew_period == Duration._from_proto(auto_renew_period)
        assert not result.receiver_signature_required
        assert result.token_relationships == []
        assert result.account_memo == "test memo"
        assert result.owned_nfts == 0

def get_account_info_responses(account_info_response):
    return [[
        response_pb2.Response(
            cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.COST_ANSWER,
                    cost=2
                )
            )
        ),
        response_pb2.Response(
            cryptoGetInfo=crypto_get_info_pb2.CryptoGetInfoResponse(
                header=response_header_pb2.ResponseHeader(
                    nodeTransactionPrecheckCode=ResponseCode.OK,
                    responseType=ResponseType.ANSWER_ONLY,
                    cost=2
                ),
                accountInfo=account_info_response
            )
        )
    ]]