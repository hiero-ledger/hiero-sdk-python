"""
Integration test for ContractExecuteTransaction.
"""

import pytest

from examples.contracts.contract_utils import (
    CONTRACT_DEPLOY_GAS,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_execute_transaction import (
    ContractExecuteTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_execute_transaction_can_execute_function(env):
    """Test that the ContractExecuteTransaction can execute a contract function successfully."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    params = ContractFunctionParameters().add_bytes32(b"Initial message from constructor")
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    new_message = b"Updated message from execute".ljust(32, b"\x00") # pad the message to 32 bytes
    execute_params = ContractFunctionParameters().add_bytes32(new_message)
    execute_receipt = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(1000000)
        .set_function("setMessage", execute_params)
        .execute(env.client)
    )
    assert (
        execute_receipt.status == ResponseCode.SUCCESS
    ), f"Contract execute failed with status: {ResponseCode(execute_receipt.status).name}"

    result = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(1000000)
        .set_function("getMessage")
        .execute(env.client)
    )
    assert result is not None, "Contract call result should not be None"
    assert result.get_bytes32(0) == new_message


@pytest.mark.integration
def test_integration_contract_execute_fails_with_no_gas(env):
    """Test that ContractExecuteTransaction fails with no gas."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    new_message = b"Updated message from execute"
    execute_params = ContractFunctionParameters().add_bytes32(new_message)
    transaction = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_function("setMessage", execute_params)
    )

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_GAS"
    ):
        transaction.execute(env.client)


@pytest.mark.integration
def test_integration_contract_execute_fails_with_invalid_function(env):
    """Test that ContractExecuteTransaction fails with invalid function."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    new_message = b"Updated message from execute"
    execute_params = ContractFunctionParameters().add_bytes32(new_message)
    receipt = (
        ContractExecuteTransaction()
        .set_gas(1000000)
        .set_contract_id(contract_id)
        .set_function("invalidFunction", execute_params)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.CONTRACT_REVERT_EXECUTED, (
        f"Contract execute should have failed with CONTRACT_REVERT_EXECUTED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_execute_fails_with_missing_parameters(env):
    """Test that ContractExecuteTransaction fails with missing function parameters."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractExecuteTransaction()
        .set_gas(1000000)
        .set_contract_id(contract_id)
        .set_function("setMessage")  # missing parameters
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.CONTRACT_REVERT_EXECUTED, (
        f"Contract execute should have failed with CONTRACT_REVERT_EXECUTED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_execute_with_amount(env):
    """Test that ContractExecuteTransaction can execute with amount."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractExecuteTransaction()
        .set_gas(1000000)
        .set_contract_id(contract_id)
        .set_payable_amount(100)  # 100 tinybars
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    info = ContractInfoQuery().set_contract_id(contract_id).execute(env.client)
    assert info.contract_id == contract_id, "Contract ID should match"
    assert info.balance == 100, "Balance should match"


@pytest.mark.integration
def test_integration_contract_execute_fails_on_nonpayable_with_payment(env):
    """
    Test that ContractExecuteTransaction fails with CONTRACT_REVERT_EXECUTED
    when a payable amount is sent to a non-payable function.
    """
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("test contract bytecode file")
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("test contract deployment")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Sending a payable amount to a non-payable function should cause a contract revert.
    receipt = (
        ContractExecuteTransaction()
        .set_gas(1000000)
        .set_contract_id(contract_id)
        .set_payable_amount(100)
        .set_function("setMessage", ContractFunctionParameters().add_bytes32(b"test"))
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.CONTRACT_REVERT_EXECUTED, (
        f"Contract execute should have failed with CONTRACT_REVERT_EXECUTED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_execute_payable_function_with_payment(env):
    """Test that ContractExecuteTransaction can call a payable function."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .execute(env.client)
    )
    assert (
        file_receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(file_receipt.status).name}"

    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None"

    initial_message = b"Initial message from constructor"
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractExecuteTransaction()
        .set_gas(1000000)
        .set_contract_id(contract_id)
        .set_payable_amount(100)
        .set_function("setMessageAndPay", ContractFunctionParameters().add_bytes32(b"test"))
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract execute failed with status: {ResponseCode(receipt.status).name}"

    info = ContractInfoQuery().set_contract_id(contract_id).execute(env.client)
    assert info.contract_id == contract_id, "Contract ID should match"
    assert info.balance == 100, "Balance should match"

    receipt = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(1000000)
        .set_function("getMessage")
        .execute(env.client)
    )
    assert receipt is not None, "Contract call result should not be None"
    assert receipt.get_bytes32(0).strip(b"\x00") == b"test", "Message should match"
