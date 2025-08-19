"""
Integration tests for ContractBytecodeQuery.
"""

import pytest

from examples.contracts import (
    CONTRACT_DEPLOY_GAS,
    SIMPLE_CONTRACT_BYTECODE,
    SIMPLE_CONTRACT_RUNTIME_BYTECODE,
)
from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_bytecode_query_can_execute(env):
    """Test that the ContractBytecodeQuery can be executed successfully."""
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytecode)
        .set_contract_memo("contract create with bytecode")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Query the contract's runtime bytecode from the network using the contract ID
    bytecode = ContractBytecodeQuery().set_contract_id(contract_id).execute(env.client)

    # Assert that the returned bytecode matches the expected runtime bytecode from compilation
    assert bytecode.hex() == SIMPLE_CONTRACT_RUNTIME_BYTECODE, "Bytecode mismatch"


@pytest.mark.integration
def test_integration_contract_bytecode_query_get_cost(env):
    """Test that the ContractBytecodeQuery can calculate query costs."""
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytecode)
        .set_contract_memo("contract create with bytecode")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    contract_bytecode = ContractBytecodeQuery().set_contract_id(contract_id)

    cost = contract_bytecode.get_cost(env.client)

    bytecode = contract_bytecode.set_query_payment(cost).execute(env.client)

    assert bytecode.hex() == SIMPLE_CONTRACT_RUNTIME_BYTECODE, "Bytecode mismatch"


@pytest.mark.integration
def test_integration_contract_bytecode_query_insufficient_payment(env):
    """Test that ContractBytecodeQuery fails with insufficient payment."""
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytecode)
        .set_contract_memo("contract create with bytecode")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    contract_bytecode = ContractBytecodeQuery().set_contract_id(contract_id)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        contract_bytecode.set_query_payment(Hbar.from_tinybars(1)).execute(env.client)


@pytest.mark.integration
def test_integration_contract_bytecode_query_fails_with_invalid_contract_id(env):
    """Test that the ContractBytecodeQuery fails with an invalid contract ID."""
    # Create a contract ID that doesn't exist on the network
    contract_id = ContractId(0, 0, 999999999)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_CONTRACT_ID"
    ):
        ContractBytecodeQuery(contract_id).execute(env.client)
