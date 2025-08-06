"""
Integration tests for ContractInfoQuery.
"""

import pytest

from examples.contracts import CONTRACT_DEPLOY_GAS, STATEFUL_CONTRACT_BYTECODE
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_info_query_can_execute(env):
    """Test that the ContractInfoQuery can be executed successfully."""
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

    info = ContractInfoQuery().set_contract_id(contract_id).execute(env.client)

    assert str(info.contract_id) == str(contract_id), "Contract ID mismatch"
    assert (
        info.admin_key.to_bytes_raw() == env.operator_key.public_key().to_bytes_raw()
    ), "Admin key mismatch"
    assert (
        info.contract_memo == "contract create with constructor params"
    ), "Contract memo mismatch"
    assert info.balance == 0, "Contract balance should be 0"
    assert info.is_deleted == False, "Contract should not be deleted"
    assert (
        info.max_automatic_token_associations == 0
    ), "Max automatic token associations should be 0"
    assert info.token_relationships == [], "Token relationships should be empty"
    assert info.account_id.num == contract_id.contract, "Account ID mismatch"


@pytest.mark.integration
def test_integration_contract_info_query_get_cost(env):
    """Test that the ContractInfoQuery can calculate query costs."""
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

    contract_info = ContractInfoQuery().set_contract_id(contract_id)

    cost = contract_info.get_cost(env.client)

    info = contract_info.set_query_payment(cost).execute(env.client)

    assert str(info.contract_id) == str(contract_id), "Contract ID mismatch"


@pytest.mark.integration
def test_integration_contract_info_query_insufficient_payment(env):
    """Test that ContractInfoQuery fails with insufficient payment."""
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

    contract_info = ContractInfoQuery().set_contract_id(contract_id)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        contract_info.set_query_payment(Hbar.from_tinybars(1)).execute(env.client)


@pytest.mark.integration
def test_integration_contract_info_query_fails_with_invalid_contract_id(env):
    """Test that the ContractInfoQuery fails with an invalid contract ID."""
    # Create a contract ID that doesn't exist on the network
    contract_id = ContractId(0, 0, 999999999)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_CONTRACT_ID"
    ):
        ContractInfoQuery(contract_id).execute(env.client)
