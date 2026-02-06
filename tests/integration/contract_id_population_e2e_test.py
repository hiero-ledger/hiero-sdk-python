"""
Integration tests for ContractId.
"""

import pytest

from examples.contract.contracts.contract_utils import (
    CONTRACT_DEPLOY_GAS,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import env, wait_for_mirror_node


@pytest.mark.integration
def test_populate_contract_id_num(env):
    """Test populate ContractId num from mirror node."""
    # Create a contract transaction
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("integration test contract")
        .execute(env.client)
    )
    assert file_receipt.status == ResponseCode.SUCCESS
    file_id = file_receipt.file_id
    assert file_id is not None

    constructor_params = ContractFunctionParameters().add_bytes32(
        b"Initial message from constructor"
    )
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(constructor_params)
        .set_bytecode_file_id(file_id)
        .execute(env.client)
    )
    assert contract_receipt.status == ResponseCode.SUCCESS

    created_contract_id = contract_receipt.contract_id
    assert created_contract_id is not None

    # Query contract info to get evm_address
    info = ContractInfoQuery().set_contract_id(created_contract_id).execute(env.client)
    contract_with_evm = ContractId.from_evm_address(0, 0, info.contract_account_id)
    assert contract_with_evm.contract == 0

    # Wait for mirror_node to update
    resolved_contract_id = wait_for_mirror_node(
        fn=lambda: contract_with_evm.populate_contract_num(env.client),
        predicate=lambda contract: contract.contract != 0,
    )

    assert resolved_contract_id.shard == created_contract_id.shard
    assert resolved_contract_id.realm == created_contract_id.realm
    assert resolved_contract_id.contract == created_contract_id.contract
    assert resolved_contract_id.evm_address == contract_with_evm.evm_address
