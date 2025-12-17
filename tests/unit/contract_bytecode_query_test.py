"""
Unit tests for ContractBytecodeQuery.
"""

from unittest.mock import Mock

import pytest

from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import (
    contract_get_bytecode_pb2,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of ContractBytecodeQuery."""
    contract_id = ContractId(0, 0, 100)

    # Test default constructor
    query = ContractBytecodeQuery()
    assert query.contract_id is None

    # Test constructor with contract_id
    query = ContractBytecodeQuery(contract_id)
    assert query.contract_id == contract_id


def test_set_contract_id():
    """Test setting contract ID with method chaining."""
    contract_id = ContractId(0, 0, 100)
    query = ContractBytecodeQuery()

    result = query.set_contract_id(contract_id)

    # Should return self for method chaining
    assert result is query
    assert query.contract_id == contract_id


def test_set_contract_id_with_none():
    """Test setting contract ID to None."""
    contract_id = ContractId(0, 0, 100)
    query = ContractBytecodeQuery(contract_id)

    result = query.set_contract_id(None)

    assert result is query
    assert query.contract_id is None


def test_execute_fails_with_missing_contract_id(mock_client):
    """Test request creation with missing Contract ID."""
    query = ContractBytecodeQuery()

    with pytest.raises(
        ValueError, match="Contract ID must be set before making the request."
    ):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = ContractBytecodeQuery()

    mock_channel = Mock()
    mock_smart_contract_stub = Mock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_smart_contract_stub.ContractGetBytecode


def test_make_request_with_missing_contract_id():
    """Test _make_request raises ValueError when contract ID is missing."""
    query = ContractBytecodeQuery()

    with pytest.raises(
        ValueError, match="Contract ID must be set before making the request."
    ):
        query._make_request()


def test_get_query_response():
    """Test _get_query_response extracts the correct response object."""
    query = ContractBytecodeQuery()

    # Create mock response
    mock_response = Mock()
    mock_bytecode_response = Mock()
    mock_response.contractGetBytecodeResponse = mock_bytecode_response

    result = query._get_query_response(mock_response)

    assert result == mock_bytecode_response


def test_contract_bytecode_query_execute():
    """Test basic functionality of ContractBytecodeQuery with mock server."""
    contract_id = ContractId(0, 0, 100)
    test_bytecode = b"608060405234801561001057600080fd5b50"

    response_sequences = get_contract_bytecode_responses(test_bytecode)

    with mock_hedera_servers(response_sequences) as client:
        query = ContractBytecodeQuery(contract_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert result == test_bytecode


def test_contract_bytecode_query_execute_with_large_bytecode():
    """Test ContractBytecodeQuery execution with large bytecode."""
    contract_id = ContractId(0, 0, 100)
    # Create a larger bytecode string to test handling of bigger responses
    test_bytecode = b"608060405234801561001057600080fd5b50" * 100

    response_sequences = get_contract_bytecode_responses(test_bytecode)

    with mock_hedera_servers(response_sequences) as client:
        query = ContractBytecodeQuery(contract_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert result == test_bytecode
        assert len(result) == len(test_bytecode)


def get_contract_bytecode_responses(bytecode_data):
    """Get the responses for the contract bytecode query."""
    return [
        [
            response_pb2.Response(
                contractGetBytecodeResponse=contract_get_bytecode_pb2.ContractGetBytecodeResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractGetBytecodeResponse=contract_get_bytecode_pb2.ContractGetBytecodeResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractGetBytecodeResponse=contract_get_bytecode_pb2.ContractGetBytecodeResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    bytecode=bytecode_data,
                )
            ),
        ]
    ]
