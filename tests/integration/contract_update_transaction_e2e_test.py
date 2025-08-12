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

    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"



@pytest.mark.integration
def test_integration_contract_update_transaction_error_when_contract_id_not_set(env):
    """Test that contract update fails when contract ID is not set."""
    # Create file with smart contract bytecode for setup
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("[e2e::ContractUpdateTransaction] error test file")
        .execute(env.client)
    )

    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create contract for cleanup purposes
    message = "Hello from Hedera.".encode("utf-8")
    params = ContractFunctionParameters().add_bytes32(message)

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("[e2e::ContractCreateTransaction] error test")
        .execute(env.client)
    )

    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Try to update contract without setting contract ID - should fail
    error_occurred = False
    try:
        update_receipt = (
            ContractUpdateTransaction()
            .set_contract_memo("[e2e::ContractUpdateTransaction] should fail")
            .execute(env.client)
        )
        # If we reach here, the transaction didn't fail as expected
        if update_receipt.status == ResponseCode.INVALID_CONTRACT_ID:
            error_occurred = True
    except Exception as e:
        # Check if it's the expected error
        if "Missing required ContractID" in str(e) or "INVALID_CONTRACT_ID" in str(e):
            error_occurred = True
        else:
            # Re-raise if it's an unexpected error
            raise e


    # Assert that the expected error occurred
    assert error_occurred, "Contract update should have failed when contract ID is not set"


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

    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"

