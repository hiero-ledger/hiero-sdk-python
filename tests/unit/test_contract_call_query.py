"""
Unit tests for the ContractCallQuery class.
"""

from unittest.mock import Mock

import pytest
from google.protobuf.wrappers_pb2 import BytesValue, Int64Value

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import (
    contract_types_pb2,
    response_header_pb2,
    response_pb2, contract_call_local_pb2
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_constructor():
    """Test initialization of ContractCallQuery."""
    contract_id = ContractId(0, 0, 2)
    account_id = AccountId(0, 0, 1)

    query = ContractCallQuery()
    assert query.contract_id is None
    assert query.gas is None
    assert query.max_result_size is None
    assert query.function_parameters is None
    assert query.sender is None

    query = ContractCallQuery(
        contract_id=contract_id,
        gas=100000,
        max_result_size=1024,
        function_parameters=b"test_params",
        sender=account_id,
    )
    assert query.contract_id == contract_id
    assert query.gas == 100000
    assert query.max_result_size == 1024
    assert query.function_parameters == b"test_params"
    assert query.sender == account_id


def test_setters_combined():
    """Test setting all properties using setters in a chain."""
    contract_id = ContractId(0, 0, 2)
    gas = 100000
    max_result_size = 1024
    sender_account = AccountId(0, 0, 1)
    function_params_only = ContractFunctionParameters().add_string("test_param")
    function_params_with_name = ContractFunctionParameters("testFunction").add_string(
        "test_param"
    )

    query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(gas)
        .set_max_result_size(max_result_size)
        .set_function("testFunction", function_params_with_name)
        .set_sender(sender_account)
    )

    assert query.contract_id == contract_id
    assert query.gas == gas
    assert query.max_result_size == max_result_size
    assert query.function_parameters == function_params_with_name.to_bytes()
    assert query.sender == sender_account

    # Test setting function parameters with ContractFunctionParameters
    query.set_function_parameters(function_params_only)
    assert query.function_parameters == function_params_only.to_bytes()

    # Test setting function parameters with bytes
    query.set_function_parameters(function_params_only.to_bytes())
    assert query.function_parameters == function_params_only.to_bytes()

    # Test set_function with default parameters
    query.set_function("testFunction")
    assert (
        query.function_parameters
        == ContractFunctionParameters("testFunction").to_bytes()
    )


def test_execute_fails_with_missing_contract_id(mock_client):
    """Test request creation with missing Contract ID."""
    query = ContractCallQuery()

    with pytest.raises(
        ValueError, match="Contract ID must be set before making the request."
    ):
        query.execute(mock_client)


def test_get_method():
    """Test retrieving the gRPC method for the query."""
    query = ContractCallQuery()

    mock_channel = Mock()
    mock_smart_contract_stub = Mock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = query._get_method(mock_channel)

    assert method.transaction is None
    assert method.query == mock_smart_contract_stub.contractCallLocalMethod


def test_contract_call_query_execute(contract_id):
    """Test basic functionality of ContractCallQuery with mock server."""
    account_id = AccountId(0, 0, 1)

    # Create contract function result with test data
    function_result = contract_types_pb2.ContractFunctionResult(
        contractID=contract_id._to_proto(),
        contractCallResult=b"test_result",
        errorMessage="",
        bloom=b"test_bloom",
        gasUsed=50000,
        evm_address=BytesValue(value=b"test_evm_address"),
        gas=100000,
        amount=0,
        functionParameters=b"test_function_params",
        signer_nonce=Int64Value(value=1),
    )

    response_sequences = get_contract_call_responses(function_result)

    with mock_hedera_servers(response_sequences) as client:
        query = ContractCallQuery(contract_id)
        query.set_gas(100000)
        query.set_max_result_size(1024)
        query.set_function_parameters(b"test_params")
        query.set_sender(account_id)

        # Get cost and verify it matches expected value
        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert isinstance(result, ContractFunctionResult)
        assert result.contract_id == contract_id
        assert result.contract_call_result == b"test_result"
        assert result.error_message == ""
        assert result.bloom == b"test_bloom"
        assert result.gas_used == 50000
        assert result.gas_available == 100000
        assert result.amount == 0
        assert result.function_parameters == b"test_function_params"
        assert result.signer_nonce == 1


def test_contract_call_query_with_function_setup(contract_id):
    """Test ContractCallQuery with function setup."""
    account_id = AccountId(0, 0, 1)

    # Create contract function result with test data
    function_result = contract_types_pb2.ContractFunctionResult(
        contractID=contract_id._to_proto(),
        contractCallResult=b"test_result",
        errorMessage="",
        bloom=b"test_bloom",
        gasUsed=50000,
        evm_address=BytesValue(value=b"test_evm_address"),
        gas=100000,
        amount=0,
        functionParameters=b"test_function_params",
        signer_nonce=Int64Value(value=1),
    )

    response_sequences = get_contract_call_responses(function_result)

    with mock_hedera_servers(response_sequences) as client:
        query = ContractCallQuery(contract_id)
        query.set_gas(100000)
        query.set_max_result_size(1024)
        query.set_sender(account_id)

        # Set function with parameters
        params = ContractFunctionParameters("testFunction")
        params.add_string("test_param")
        query.set_function("testFunction", params)

        cost = query.get_cost(client)
        assert cost.to_tinybars() == 2

        # Execute query and get result
        result = query.execute(client)

        assert isinstance(result, ContractFunctionResult)
        assert result.contract_id == contract_id
        assert result.contract_call_result == b"test_result"


def get_contract_call_responses(function_result):
    return [
        [
            response_pb2.Response(
                contractCallLocal=contract_call_local_pb2.ContractCallLocalResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractCallLocal=contract_call_local_pb2.ContractCallLocalResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                contractCallLocal=contract_call_local_pb2.ContractCallLocalResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    functionResult=function_result,
                )
            ),
        ]
    ]
