"""
Integration tests for the ContractCreateTransaction class.
"""

import pytest

from examples.contracts import (
    CONTRACT_DEPLOY_GAS,
    SIMPLE_CONTRACT_BYTECODE,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_create_transaction_can_execute(env):
    """Test that a contract can be created and executed."""
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


@pytest.mark.integration
def test_integration_contract_create_transaction_with_constructor(env):
    """Test that a contract can be created with constructor parameters."""
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("file create with constructor params")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Convert the message string to bytes32 format for the contract constructor.
    message = "Initial message from constructor".encode("utf-8")

    params = ContractFunctionParameters().add_bytes32(message)

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(params)
        .set_contract_memo("contract create with constructor params")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"


@pytest.mark.integration
def test_integration_contract_create_transaction_set_bytecode(env):
    """Test that a contract can be created with bytecode."""
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytecode)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"
