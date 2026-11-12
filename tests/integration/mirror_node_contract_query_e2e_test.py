"""
Integration tests for MirrorNodeContractCallQuery and MirrorNodeContractEstimateGasQuery.

The mirror node lags consensus by a few seconds, so every query against a
freshly deployed or freshly updated contract polls with wait_for_mirror_node.
"""

from __future__ import annotations

import pytest

from examples.contract.contracts.contract_utils import (
    CONTRACT_DEPLOY_GAS,
    STATEFUL_CONTRACT_BYTECODE,
)
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_execute_transaction import (
    ContractExecuteTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.exceptions import MirrorNodeError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.query.mirror_node_contract_call_query import (
    MirrorNodeContractCallQuery,
)
from hiero_sdk_python.query.mirror_node_contract_estimate_gas_query import (
    MirrorNodeContractEstimateGasQuery,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import wait_for_mirror_node


# Exactly 32 bytes, so the bytes32 round trip has no zero padding.
INITIAL_MESSAGE = b"Initial message from constructor"
UPDATED_MESSAGE = b"Updated message via mirror gas.."
MIRROR_TIMEOUT = 30


def _deploy_stateful_contract(env) -> ContractId:
    """Deploy StatefulContract with INITIAL_MESSAGE as the constructor argument."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .execute(env.client)
    )
    assert file_receipt.status == ResponseCode.SUCCESS

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_constructor_parameters(ContractFunctionParameters().add_bytes32(INITIAL_MESSAGE))
        .set_bytecode_file_id(file_receipt.file_id)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.contract_id is not None

    return receipt.contract_id


def _decode_bytes32(result_hex: str) -> bytes:
    return ContractFunctionResult(contract_call_result=bytes.fromhex(result_hex[2:])).get_bytes32(0)


def _wait_for_message(env, query: MirrorNodeContractCallQuery, expected: bytes) -> str:
    """
    Poll the mirror node until the getMessage call returns the expected message.

    Before the mirror node imports the contract, the call returns "0x" (a call to an
    address with no code), so an empty result means "not there yet".
    """
    return wait_for_mirror_node(
        fn=lambda: query.execute(env.client),
        predicate=lambda result: result != "0x" and _decode_bytes32(result) == expected,
        timeout=MIRROR_TIMEOUT,
    )


@pytest.mark.integration
def test_call_view_function_returns_abi_encoded_result(env):
    """A view function call returns the ABI-encoded value the contract holds."""
    contract_id = _deploy_stateful_contract(env)

    query = MirrorNodeContractCallQuery().set_contract_id(contract_id).set_sender(env.operator_id)
    query.set_function("getMessage")

    result = _wait_for_message(env, query, INITIAL_MESSAGE)

    assert result.startswith("0x")
    assert len(result) == 2 + 64
    assert _decode_bytes32(result) == INITIAL_MESSAGE


@pytest.mark.integration
def test_call_with_contract_evm_address_only(env):
    """set_contract_evm_address works without set_contract_id."""
    contract_id = _deploy_stateful_contract(env)

    query = (
        MirrorNodeContractCallQuery()
        .set_contract_evm_address("0x" + contract_id.to_evm_address())
        .set_function("getMessage")
    )

    result = _wait_for_message(env, query, INITIAL_MESSAGE)

    assert query.contract_id is None
    assert _decode_bytes32(result) == INITIAL_MESSAGE


@pytest.mark.integration
def test_estimated_gas_is_enough_to_execute(env):
    """An estimate for a state-changing call is positive and enough for ContractExecuteTransaction."""
    contract_id = _deploy_stateful_contract(env)
    params = ContractFunctionParameters().add_bytes32(UPDATED_MESSAGE)

    # Until the mirror node imports the contract, an estimate succeeds as a plain
    # transfer to an empty address and is too low, so wait for the contract first.
    _wait_for_message(
        env, MirrorNodeContractCallQuery().set_contract_id(contract_id).set_function("getMessage"), INITIAL_MESSAGE
    )

    gas = wait_for_mirror_node(
        fn=lambda: (
            MirrorNodeContractEstimateGasQuery()
            .set_contract_id(contract_id)
            .set_sender(env.operator_id)
            .set_function("setMessage", params)
            .execute(env.client)
        ),
        predicate=lambda estimate: estimate > 0,
        timeout=MIRROR_TIMEOUT,
    )

    assert isinstance(gas, int)
    assert gas > 0

    receipt = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(gas)
        .set_function("setMessage", ContractFunctionParameters().add_bytes32(UPDATED_MESSAGE))
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Contract execution failed with status: {ResponseCode(receipt.status).name}"
    )

    # The simulated call sees the new state once the mirror node has caught up.
    query = MirrorNodeContractCallQuery().set_contract_id(contract_id).set_function("getMessage")
    assert _decode_bytes32(_wait_for_message(env, query, UPDATED_MESSAGE)) == UPDATED_MESSAGE


@pytest.mark.integration
@pytest.mark.parametrize("query_class", [MirrorNodeContractCallQuery, MirrorNodeContractEstimateGasQuery])
def test_revert_raises_with_revert_reason(env, query_class):
    """A call that reverts raises MirrorNodeError carrying the contract's revert message."""
    contract_id = _deploy_stateful_contract(env)
    not_owner = env.create_account()
    revert_reason = "Only the owner can update the message."

    def call():
        try:
            query_class().set_contract_id(contract_id).set_sender(not_owner.id).set_function(
                "setMessageAndPay", ContractFunctionParameters().add_bytes32(UPDATED_MESSAGE)
            ).execute(env.client)
        except MirrorNodeError as error:
            return error
        return None

    # Until the mirror node has the contract and the account, it may answer differently.
    error = wait_for_mirror_node(
        fn=call,
        predicate=lambda err: err is not None and revert_reason in str(err),
        timeout=MIRROR_TIMEOUT,
    )

    assert error.status_code == 400
    assert any(revert_reason in message for message in error.messages)


@pytest.mark.integration
def test_execute_without_contract_raises_value_error(env):
    """No contract set raises ValueError before any request is sent."""
    with pytest.raises(ValueError, match="contract_id or contract_evm_address must be set"):
        MirrorNodeContractCallQuery().set_function("getMessage").execute(env.client)

    with pytest.raises(ValueError, match="contract_id or contract_evm_address must be set"):
        MirrorNodeContractEstimateGasQuery().set_function("getMessage").execute(env.client)
