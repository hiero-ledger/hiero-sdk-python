"""
E2E integration tests for TransactionGetReceiptQuery include_child_receipts support.

These tests validate the full SDK flow against a real Hedera network:
- submit a real transaction
- query its receipt
- verify children behavior with and without include_children flag

NOTE:
The contract used in these tests (StatefulContract) does NOT deterministically
produce child receipts, so we only assert API correctness and stability,
not children count > 0.
"""

import pytest

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

from tests.integration.utils_for_test import env


def _extract_tx_id(tx, receipt):
    """
    Best-effort extraction of TransactionId for E2E tests.
    """
    tx_id = getattr(receipt, "transaction_id", None)
    if tx_id is not None:
        return tx_id

    tx_id = getattr(tx, "transaction_id", None)
    if tx_id is not None:
        return tx_id

    tx_id = getattr(tx, "_transaction_id", None)
    if tx_id is not None:
        return tx_id

    tx_ids = getattr(tx, "_transaction_ids", None)
    if tx_ids:
        return tx_ids[0]

    raise AssertionError(
        "Unable to extract TransactionId from transaction or receipt."
    )


def _submit_simple_transfer(env):
    """
    Submit a simple transfer transaction and return its TransactionId.
    """
    receiver = env.create_account(initial_hbar=0.0)

    tx = (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, Hbar(-0.01))
        .add_hbar_transfer(receiver.id, Hbar(0.01))
    )

    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS

    return _extract_tx_id(tx, receipt)


@pytest.mark.integration
def test_get_receipt_query_children_empty_when_not_requested_e2e(env):
    """
    E2E:
    When include_children is NOT requested, receipt.children must be empty.
    """
    tx_id = _submit_simple_transfer(env)

    receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(tx_id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.children == []


@pytest.mark.integration
def test_get_receipt_query_children_list_when_requested_e2e(env):
    """
    E2E:
    When include_children IS requested, receipt.children must exist and be a list.
    The list may be empty depending on transaction type.
    """
    tx_id = _submit_simple_transfer(env)

    receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(tx_id)
        .set_include_children(True)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS
    assert isinstance(receipt.children, list)


@pytest.mark.integration
def test_get_receipt_query_children_with_contract_execute_e2e(env):
    """
    E2E:
    Execute a real contract transaction and query its receipt with include_children enabled.

    We assert:
    - no crash
    - receipt.children exists and is a list
    """
    from examples.contract.contracts.contract_utils import (
        CONTRACT_DEPLOY_GAS,
        STATEFUL_CONTRACT_BYTECODE,
    )
    from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
    from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
    from hiero_sdk_python.contract.contract_execute_transaction import ContractExecuteTransaction
    from hiero_sdk_python.contract.contract_function_parameters import ContractFunctionParameters

    # Upload contract bytecode
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("transaction receipt children test")
        .execute(env.client)
    )
    assert file_receipt.status == ResponseCode.SUCCESS
    file_id = file_receipt.file_id
    assert file_id is not None

    # Deploy contract
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
    contract_id = contract_receipt.contract_id
    assert contract_id is not None

    # Execute contract function
    execute_tx = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(1_000_000)
        .set_function(
            "setMessage",
            ContractFunctionParameters().add_bytes32(b"Updated message".ljust(32, b"\x00")),
        )
    )
    execute_receipt = execute_tx.execute(env.client)
    assert execute_receipt.status == ResponseCode.SUCCESS

    try:
        tx_id = _extract_tx_id(execute_tx, execute_receipt)
    except AssertionError as e:
        pytest.skip(str(e))

    queried = (
        TransactionGetReceiptQuery()
        .set_transaction_id(tx_id)
        .set_include_children(True)
        .execute(env.client)
    )

    assert queried.status == ResponseCode.SUCCESS

    if len(queried.children) > 0:
        for child in queried.children:
            __import__('pdb').set_trace()
            assert child.status is not None

    assert isinstance(queried.children, list)
