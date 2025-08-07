"""
Integration tests for ContractCallQuery.
"""

import pytest

from examples.contracts.contract_utils import (
    CONTRACT_DEPLOY_GAS,
    SIMPLE_CONTRACT_BYTECODE,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_call_query_can_execute_with_constructor(env):
    """Test that the ContractCallQuery can be executed successfully."""
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("some test file create transaction memo")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # The message is exactly 32 bytes, so we won't have a problem with padding zeroes.
    message = b"Initial message from constructor"
    params = ContractFunctionParameters().add_bytes32(message)

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("some test contract create transaction memo")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    result = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(10000000)
        .set_function("getMessage")
        .execute(env.client)
    )

    assert result is not None, "Contract call result should not be None"
    assert result.get_bytes32(0) == message


@pytest.mark.integration
def test_integration_contract_call_query_can_execute(env):
    """Test that the ContractCallQuery can be executed successfully."""
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("some test file create transaction memo")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("some test contract create transaction memo")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    result = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(10000000)
        .set_function("greet")
        .execute(env.client)
    )

    assert result is not None, "Contract call result should not be None"
    assert result.get_string(0) == "Hello, world!"


@pytest.mark.integration
def test_integration_contract_call_query_get_cost(env):
    """Test that the ContractCallQuery can calculate query costs."""
    # Create a file for contract bytecode
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Deploy the contract
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Prepare the contract call query
    contract_call_query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(10000000)
        .set_function("greet")
    )

    # Get the cost for the query
    cost = contract_call_query.get_cost(env.client)

    # Execute the query with the exact cost
    result = contract_call_query.set_query_payment(cost).execute(env.client)

    assert result is not None, "Contract call result should not be None"
    assert result.get_string(0) == "Hello, world!"


@pytest.mark.integration
def test_integration_contract_call_query_insufficient_payment(env):
    """Test that ContractCallQuery fails with insufficient payment."""
    # Create a file for contract bytecode
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Deploy the contract
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Prepare the contract call query with insufficient payment
    contract_call_query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(10000000)
        .set_function("greet")
    )
    contract_call_query.set_query_payment(
        Hbar.from_tinybars(1)
    )  # Intentionally insufficient

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        contract_call_query.execute(env.client)


@pytest.mark.integration
def test_integration_contract_call_query_fails_with_invalid_contract_id(env):
    """Test that ContractCallQuery fails with an invalid contract ID."""
    invalid_contract_id = ContractId(0, 0, 999999999)

    contract_call_query = (
        ContractCallQuery()
        .set_contract_id(invalid_contract_id)
        .set_gas(10000000)
        .set_function("greet")
    )

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_CONTRACT_ID"
    ):
        contract_call_query.execute(env.client)


@pytest.mark.integration
def test_integration_contract_call_query_fails_with_no_gas(env):
    """Test that ContractCallQuery fails when no gas is provided."""
    # Deploy a contract first
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("test contract for no gas")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment for no gas")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Attempt to call the contract with no gas set
    contract_call_query = (
        ContractCallQuery().set_contract_id(contract_id).set_function("greet")
    )

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_GAS"
    ):
        contract_call_query.execute(env.client)
