import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_info import TokenInfo
from hiero_sdk_python.client.client import Client
#from hiero_sdk_python.hapi.services import token_get_info_pb2
#from hiero_sdk_python.hapi.services import token_get_info_pb2
#from hiero_sdk_python.hapi.services.token_info_pb2 import TokenInfo as ProtoTokenInfo
#from hiero_sdk_python.hapi.services.token_info_pb2 import TokenInfo as ProtoTokenInfo
from hiero_sdk_python.hapi.services.response_header_pb2 import ResponseHeader
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.hapi.services import (
    token_get_info_pb2,
)

@pytest.fixture
def mock_token_info_response():
    """Fixture to provide a mock response for the token Info Query"""

    token_info = token_get_info_pb2.TokenInfo(
        name = 'TestToken',
        symbol = 'TTK',
        decimals =8
    )

    response = token_get_info_pb2.TokenGetInfoResponse(
        header = ResponseHeader(nodeTransactionPrecheckCode=0),
        tokenInfo=token_info
    )

    return response

def test_token_info_query_execute(mock_token_info_response):
    """
    Test the TokenGetInfoQuery with a mocked response. 
    """

    token_id = TokenId(0, 0, 1234)

    query = TokenInfoQuery().set_token_id(token_id)

    query.node_account_ids = [MagicMock()]
    query._make_request = MagicMock(return_value="mock_request")
    query._get_status_from_response = MagicMock(return_value=0)

    #below is new
    mapped_token_info = TokenInfo(
        tokenId=token_id,
        name="TestToken",
        symbol="TTK",
        decimals=8,
        totalSupply=0,
        treasury=None,
        isDeleted=False,
        memo="",
        tokenType=TokenType.FUNGIBLE_COMMON, 
        maxSupply=0,
        ledger_id=b"",
    )

    query._map_response = MagicMock(return_value=mock_token_info_response.tokenInfo)

    mock_client = MagicMock(spec=Client)
    mock_client.send_query = MagicMock(return_value=mock_token_info_response)

    token_info = query.execute(mock_client)

    assert token_info.name == "TestToken"
    assert token_info.symbol == "TTK"
    assert token_info.decimals == 8
