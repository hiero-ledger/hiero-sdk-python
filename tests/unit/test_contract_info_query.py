"""
Unit tests for the ContractInfoQuery class.
"""

from unittest.mock import Mock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.hapi.services import (
    contract_get_info_pb2,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of ContractInfoQuery."""
    contract_id = ContractId(0, 0, 100)

    query = ContractInfoQuery()
    assert query.contract_id is None

    query = ContractInfoQuery(contract_id)
    assert query.contract_id == contract_id


def test_set_contract_id():
    """Test setting contract ID with method chaining."""
    contract_id = ContractId(0, 0, 100)
    query = ContractInfoQuery()

    result = query.set_contract_id(contract_id)

    assert result is query  # Should return self for chaining
    assert query.contract_id == contract_id


def test_execute_fails_with_missing_contract_id(mock_client):
    """Test request creation with missing Contract ID."""
    query = ContractInfoQuery()

    with pytest.raises(
        ValueError, match="Contract ID must be set before making the request."
    ):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = ContractInfoQuery()

    mock_channel = Mock()
    mock_smart_contract_stub = Mock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_smart_contract_stub.getContractInfo


def test_contract_info_query_execute(private_key):
    """Test basic functionality of ContractInfoQuery with mock server."""
    account_id = AccountId(0, 0, 100)
    contract_id = ContractId(0, 0, 100)
    expiration_time = TimestampProto(seconds=1718745600)

    # Create contract info response with test data
    contract_info_response = contract_get_info_pb2.ContractGetInfoResponse.ContractInfo(
        contractID=contract_id._to_proto(),
        accountID=account_id._to_proto(),
        contractAccountID="0.0.100",
        max_automatic_token_associations=0,
        tokenRelationships=[],
        adminKey=private_key.public_key()._to_proto(),
        expirationTime=expiration_time,
        storage=2048,
        memo="test contract memo",
        balance=1000000,
        deleted=False,
    )

    response_sequences = get_contract_info_responses(contract_info_response)

    with mock_hedera_servers(response_sequences) as client:
        query = ContractInfoQuery(contract_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert result.contract_id == contract_id
        assert result.contract_account_id == "0.0.100"
        assert (
            result.admin_key.to_bytes_raw() == private_key.public_key().to_bytes_raw()
        )
        assert result.expiration_time == Timestamp._from_protobuf(expiration_time)
        assert result.storage == 2048
        assert result.contract_memo == "test contract memo"
        assert result.balance == 1000000
        assert not result.is_deleted
        assert result.max_automatic_token_associations == 0
        assert not result.token_relationships
        assert result.account_id == account_id


def get_contract_info_responses(contract_info_response):
    """Helper function to create mock contract info responses."""
    return [
        [
            response_pb2.Response(
                contractGetInfo=contract_get_info_pb2.ContractGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractGetInfo=contract_get_info_pb2.ContractGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractGetInfo=contract_get_info_pb2.ContractGetInfoResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    contractInfo=contract_info_response,
                )
            ),
        ]
    ]
