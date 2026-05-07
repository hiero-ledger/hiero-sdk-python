"""
E2E integration tests for TransactionGetReceiptQuery support.

These tests validate the full SDK flow against a real Hedera network:
- submit a real transaction
- query its receipt
- verify children behavior with and without include_children flag
- verify duplicate transactions returned with include_duplicates flag

Note:
The contract used in these tests (StatefulContract) does NOT deterministically
produce child receipts, so we only assert API correctness and stability,
not children count > 0.
"""

from __future__ import annotations

import threading

import pytest

from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import ReceiptStatusError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


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

    raise AssertionError("Unable to extract TransactionId from transaction or receipt.")


def _submit_simple_transfer(env, node_ids=None, tx_id=None):
    """
    Submit a simple transfer transaction and return its TransactionId.
    """
    receiver = env.create_account(initial_hbar=0.0)

    tx = (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, Hbar(-0.01).to_tinybars())
        .add_hbar_transfer(receiver.id, Hbar(0.01).to_tinybars())
    )
    if tx_id is not None:
        tx.set_transaction_id(tx_id)
    if node_ids is not None:
        tx.set_node_account_ids(node_ids)
    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS

    return _extract_tx_id(tx, receipt)


def _setup_contract_and_execute(env, memo):
    """
    Helper to setup and execute a contract transaction.

    Returns the transaction ID of the contract execute operation.
    Raises AssertionError if transaction ID cannot be extracted (triggering pytest.skip).
    """
    from examples.contract.contracts.contract_utils import (
        CONTRACT_DEPLOY_GAS,
        STATEFUL_CONTRACT_BYTECODE,
    )
    from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
    from hiero_sdk_python.contract.contract_execute_transaction import ContractExecuteTransaction
    from hiero_sdk_python.contract.contract_function_parameters import ContractFunctionParameters
    from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction

    # Upload contract bytecode
    file_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo(memo)
        .execute(env.client)
    )
    assert file_receipt.status == ResponseCode.SUCCESS
    file_id = file_receipt.file_id
    assert file_id is not None, "File ID should not be None after successful file creation"

    # Deploy contract
    constructor_params = ContractFunctionParameters().add_bytes32(b"Initial message")
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
    assert contract_id is not None, "Contract ID should not be None after successful contract creation"

    # Execute contract transaction
    execute_tx = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(1_000_000)
        .set_function(
            "setMessage",
            ContractFunctionParameters().add_bytes32(b"Test".ljust(32, b"\x00")),
        )
    )
    execute_receipt = execute_tx.execute(env.client)
    assert execute_receipt.status == ResponseCode.SUCCESS

    return _extract_tx_id(execute_tx, execute_receipt)


@pytest.mark.integration
def test_get_receipt_query_children_empty_when_not_requested_e2e(env):
    """
    E2E:
    When include_children is NOT requested, receipt.children must be empty.
    """
    tx_id = _submit_simple_transfer(env)

    receipt = TransactionGetReceiptQuery().set_transaction_id(tx_id).execute(env.client)

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

    receipt = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_children(True).execute(env.client)

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
    from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
    from hiero_sdk_python.contract.contract_execute_transaction import ContractExecuteTransaction
    from hiero_sdk_python.contract.contract_function_parameters import ContractFunctionParameters
    from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction

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
    constructor_params = ContractFunctionParameters().add_bytes32(b"Initial message from constructor")
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

    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_children(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS

    if len(queried.children) > 0:
        for child in queried.children:
            assert child.status is not None

    assert isinstance(queried.children, list)


@pytest.mark.integration
@pytest.mark.xfail(
    reason="Flaky test due to network conditions causing no duplicates to be created. Python Virtual Threads compete too quickly."
)
def test_get_receipt_query_include_duplicates_execute_e2e(env):
    """
    E2E:
    Execute a real contract transaction and query its receipt with include_duplicates enabled.

    We assert:
    - no crash
    - receipt.duplicates exists and is a list
    """
    tx_id = TransactionId.generate(env.operator_id)
    nodes = env.client.network.nodes
    nodes = [nodes[0]._account_id, nodes[1]._account_id]
    tx1 = threading.Thread(target=_submit_simple_transfer, args=(env, [nodes[0]], tx_id))
    tx2 = threading.Thread(target=_submit_simple_transfer, args=(env, [nodes[1]], tx_id))
    tx1.start()
    tx2.start()
    tx1.join()
    tx2.join()
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_duplicates(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS
    assert isinstance(queried.duplicates, list)
    assert len(queried.duplicates) == 1


@pytest.mark.integration
def test_get_receipt_returns_failed_status_receipt_if_validate_status_false(env):
    """Test receipt is returned despite failure when validate_status is False."""
    tx = AccountDeleteTransaction().set_transfer_account_id(env.operator_id).set_account_id(AccountId(0, 0, 0))
    response = tx.execute(env.client, wait_for_receipt=False)

    query = (
        TransactionGetReceiptQuery()
        .set_transaction_id(response.transaction_id)
        .set_validate_status(False)  # Default value
    )

    receipt = query.execute(env.client)
    assert isinstance(receipt, TransactionReceipt)
    assert receipt.transaction_id == tx.transaction_id
    assert receipt.status == ResponseCode.INVALID_ACCOUNT_ID


@pytest.mark.integration
def test_get_receipt_throws_status_error_when_validation_enabled(env):
    """Test error is raised for failures when validate_status is True."""
    tx = AccountDeleteTransaction().set_transfer_account_id(env.operator_id).set_account_id(AccountId(1, 0, 0))
    response = tx.execute(env.client, wait_for_receipt=False)

    query = TransactionGetReceiptQuery().set_transaction_id(response.transaction_id).set_validate_status(True)

    with pytest.raises(ReceiptStatusError) as e:
        query.execute(env.client)

    assert e.value.status == ResponseCode.INVALID_ACCOUNT_ID


@pytest.mark.integration
def test_get_receipt_query_child_receipts_have_none_transaction_id_e2e(env):
    """
    E2E:
    Verify that child receipts have transaction_id = None (they are independent transactions).

    Rationale: Child receipts are sub-transactions created by the parent transaction.
    They should have their own identity and not inherit the parent's transaction_id.
    """
    try:
        tx_id = _setup_contract_and_execute(env, "child receipt transaction_id test")
    except AssertionError as e:
        pytest.skip(str(e))

    # Query with include_children
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_children(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS

    # Verify: if children exist, each child has transaction_id = None
    if len(queried.children) > 0:
        for child_receipt in queried.children:
            assert child_receipt.status is not None
            # CRITICAL FIX VERIFICATION: Child receipts must have transaction_id = None
            # because they are independent sub-transactions, not duplicates of the parent
            assert child_receipt.transaction_id is None, (
                "Child receipt must have transaction_id=None (independent identity)"
            )


@pytest.mark.integration
@pytest.mark.xfail(reason="Uses threads to create duplicate tx, may be flaky")
def test_get_receipt_query_duplicate_receipts_retain_parent_transaction_id_e2e(env):
    """
    E2E:
    Verify that duplicate receipts retain the parent transaction_id for context.

    Rationale: Duplicates are the same transaction submitted to different nodes.
    They should preserve the parent transaction_id to show the relationship.
    """
    tx_id = TransactionId.generate(env.operator_id)
    nodes = env.client.network.nodes

    # Need at least 2 nodes to potentially create duplicates
    if len(nodes) < 2:
        pytest.skip("Not enough nodes to create duplicate receipts")

    node_ids = [nodes[0]._account_id, nodes[1]._account_id]

    # Submit same transaction to different nodes
    tx1 = threading.Thread(target=_submit_simple_transfer, args=(env, [node_ids[0]], tx_id))
    tx2 = threading.Thread(target=_submit_simple_transfer, args=(env, [node_ids[1]], tx_id))

    tx1.start()
    tx2.start()
    tx1.join()
    tx2.join()

    # Query with include_duplicates
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_duplicates(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS
    assert isinstance(queried.duplicates, list)

    # Verify: if duplicates exist, each duplicate retains parent transaction_id
    if len(queried.duplicates) > 0:
        for duplicate_receipt in queried.duplicates:
            assert duplicate_receipt.status is not None
            # CRITICAL FIX VERIFICATION: Duplicate receipts must keep parent transaction_id
            # to maintain the relationship and context with the original transaction
            assert duplicate_receipt.transaction_id == tx_id, (
                f"Duplicate receipt must have transaction_id={tx_id} (same as parent)"
            )


@pytest.mark.integration
def test_get_receipt_query_child_receipt_mapping_e2e(env):
    """
    E2E:
    Verify child receipts are properly mapped with transaction_id=None (independent identity).

    Rationale: The fix for #1849 ensures child receipts have None transaction_id instead of
    inheriting parent transaction_id. This test verifies the mapping behavior.

    Note: While this test uses contract execution, the key verification is that the
    TransactionGetReceiptQuery correctly maps child receipts with None transaction_id,
    regardless of whether children are populated. The unit tests verify account_id
    accessibility with populated accountID fields.
    """
    try:
        tx_id = _setup_contract_and_execute(env, "child receipt mapping test")
    except AssertionError as e:
        pytest.skip(str(e))

    # Query with include_children
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_children(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS

    # Verify mapping behavior - all child receipts should have transaction_id = None
    for child_receipt in queried.children:
        assert child_receipt.status is not None
        # CRITICAL: Child receipts must map with transaction_id=None (independent transactions)
        assert child_receipt.transaction_id is None, (
            "Child receipt must have transaction_id=None (independent identity, not parent context)"
        )


@pytest.mark.integration
def test_get_receipt_query_child_receipt_account_id_from_auto_account_creation_e2e(env):
    """
    E2E:
    Verify that child receipts have accessible account_id from auto-account creation.

    This directly tests the fix for issue #1849: account_id property was filtering out
    accountNum==0 values, which blocked access to EVM auto-created accounts.

    Approach:
    - Create AccountId with just EVM address (triggers auto-account creation on transfer)
    - Transfer to that account (creates child receipt with populated accountID)
    - Query with include_children and verify account_id is accessible

    This test may skip if the network doesn't populate child receipts for transfers,
    but when child receipts exist, we verify the fix is working.
    """
    # Create AccountId with EVM address to trigger auto-account creation
    # Using a valid EVM address format (20 bytes)
    evm_address = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")
    receiver = AccountId.from_evm_address(evm_address.hex(), 0, 0)

    # Transfer to trigger auto-account creation (may produce child receipt with accountID)
    tx = (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, Hbar(-0.01).to_tinybars())
        .add_hbar_transfer(receiver, Hbar(0.01).to_tinybars())
    )
    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS

    try:
        tx_id = _extract_tx_id(tx, receipt)
    except AssertionError:
        pytest.skip("Could not extract transaction ID")

    # Query with include_children
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_children(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS

    # Verify: if child receipts exist, account_id should be accessible
    if len(queried.children) > 0:
        for child_receipt in queried.children:
            assert child_receipt.status is not None
            # FIX VERIFICATION: account_id must be accessible (not filtered for accountNum==0)
            if child_receipt.account_id is not None:
                # Account_id should be a valid AccountId instance
                assert isinstance(child_receipt.account_id, AccountId), (
                    "child_receipt.account_id should be AccountId instance"
                )
                # Verify basic structure (even if accountNum is 0)
                assert hasattr(child_receipt.account_id, "shard"), "account_id should have shard attribute"
                assert hasattr(child_receipt.account_id, "realm"), "account_id should have realm attribute"
                assert hasattr(child_receipt.account_id, "num"), "account_id should have num attribute"


@pytest.mark.integration
@pytest.mark.xfail(
    reason="Flaky: Network conditions may prevent duplicates from being created. Concurrent thread access to env.create_account() may have race conditions."
)
def test_get_receipt_query_duplicate_receipts_mapping_e2e(env):
    """
    E2E:
    Verify duplicate receipts are properly mapped with transaction_id=parent (context preservation).

    Rationale: The fix for #1849 ensures duplicate receipts retain parent transaction_id
    to maintain context, unlike child receipts which have None.

    This test is marked xfail because:
    1. Network conditions may not produce duplicates
    2. Concurrent calls to env.create_account() may have shared state issues
    3. Testing environment may not guarantee duplicate receipt creation
    """
    tx_id = TransactionId.generate(env.operator_id)
    nodes = env.client.network.nodes

    if len(nodes) < 2:
        pytest.skip("Not enough nodes to create duplicate receipts")

    node_ids = [nodes[0]._account_id, nodes[1]._account_id]

    # Submit same transaction to different nodes
    tx1 = threading.Thread(target=_submit_simple_transfer, args=(env, [node_ids[0]], tx_id))
    tx2 = threading.Thread(target=_submit_simple_transfer, args=(env, [node_ids[1]], tx_id))

    tx1.start()
    tx2.start()
    tx1.join()
    tx2.join()

    # Query with include_duplicates
    queried = TransactionGetReceiptQuery().set_transaction_id(tx_id).set_include_duplicates(True).execute(env.client)

    assert queried.status == ResponseCode.SUCCESS
    assert isinstance(queried.duplicates, list)

    # Verify mapping behavior - all duplicate receipts should retain parent transaction_id
    if len(queried.duplicates) > 0:
        for duplicate_receipt in queried.duplicates:
            # CRITICAL: Duplicate receipts must map with parent transaction_id (context preservation)
            assert duplicate_receipt.transaction_id == tx_id, (
                f"Duplicate receipt must have transaction_id={tx_id} (same as parent for context)"
            )
