"""
Integration tests for the ContractUpdateTransaction class.
"""

import pytest

from examples.contracts import (
    CONTRACT_DEPLOY_GAS,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateTransaction,
)
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_update_transaction_can_execute(env):
    """Test that a contract can be updated successfully."""
    # Create file with smart contract bytecode
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("[e2e::ContractUpdateTransaction] bytecode file")
        .execute(env.client)
    )

    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"
    assert file_id.file > 0, "File ID number should be greater than 0"

    # Create contract with constructor parameters
    # Convert the message string to bytes32 format for the contract constructor
    message = "Hello from Hedera.".encode("utf-8")
    params = ContractFunctionParameters().add_bytes32(message)

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("[e2e::ContractCreateTransaction]")
        .execute(env.client)
    )

    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"
    assert contract_id.contract > 0, "Contract ID number should be greater than 0"

    # Update the contract memo
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_contract_memo("[e2e::ContractUpdateTransaction]")
        .execute(env.client)
    )

    contract_info = (
        ContractInfoQuery(env.client).set_contract_id(contract_id).execute(env.client)
    )

    assert (
        contract_info.contract_memo == "[e2e::ContractUpdateTransaction]"
    ), "Contract memo should be updated"
    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"


@pytest.mark.integration
def test_integration_contract_update_transaction_fails_with_invalid_contract_id(env):
    """Test that contract update fails when contract ID is invalid."""
    contract_id = ContractId(0, 0, 999999999)

    receipt = (
        ContractUpdateTransaction().set_contract_id(contract_id).execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_CONTRACT_ID, (
        f"Contract update should fail when contract ID is invalid, "
        f"but got status: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_update_transaction_with_admin_key(env):
    """Test that a contract admin key can be updated."""
    # Create file with smart contract bytecode
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("[e2e::ContractUpdateTransaction] admin key test")
        .execute(env.client)
    )

    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create contract with admin key
    message = "Hello from Hedera.".encode("utf-8")
    params = ContractFunctionParameters().add_bytes32(message)

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("[e2e::ContractCreateTransaction] with admin key")
        .execute(env.client)
    )

    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Update the contract with the same admin key (should work)
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(env.operator_key.public_key())
        .set_contract_memo("[e2e::ContractUpdateTransaction] admin key updated")
        .execute(env.client)
    )

    contract_info = (
        ContractInfoQuery(env.client).set_contract_id(contract_id).execute(env.client)
    )
    assert (
        contract_info.contract_memo
        == "[e2e::ContractUpdateTransaction] admin key updated"
    ), "Contract memo should be updated"
    assert (
        contract_info.admin_key.to_string() == env.operator_key.public_key().to_string()
    ), "Admin key should be updated"

    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"
