"""
Integration tests for ContractDeleteTransaction.
"""

import pytest

from examples.contracts import CONTRACT_DEPLOY_GAS, SIMPLE_CONTRACT_BYTECODE
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_delete_transaction import (
    ContractDeleteTransaction,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_delete_transaction_can_transfer_balance_to_account(env):
    """Test that the ContractDeleteTransaction can transfer the contract balance to account."""
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_initial_balance(Hbar(1).to_tinybars())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("test contract delete transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Create account with 1 HBAR initial balance
    account = env.create_account()

    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(account.id)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Delete contract failed with status: {ResponseCode(receipt.status).name}"

    contract_info = ContractInfoQuery(contract_id).execute(env.client)
    assert contract_info.is_deleted is True, "Contract should be deleted"

    account_info = AccountInfoQuery(account.id).execute(env.client)
    assert account_info.account_id == account.id, "Account ID should match"
    assert (
        account_info.balance.to_tinybars() == Hbar(2).to_tinybars()
    ), f"Account balance should be 2 HBAR but got {account_info.balance.to_tinybars()}"


@pytest.mark.integration
def test_integration_contract_delete_transaction_can_transfer_balance_to_contract(env):
    """Test that the ContractDeleteTransaction can transfer the contract balance to contract."""
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_initial_balance(Hbar(1).to_tinybars())
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("test contract delete transaction")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_initial_balance(Hbar(1).to_tinybars())
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("contract to transfer balance to")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    transfer_contract_id = receipt.contract_id
    assert transfer_contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_contract_id(transfer_contract_id)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract deletion failed with status: {ResponseCode(receipt.status).name}"

    contract_info = ContractInfoQuery(contract_id).execute(env.client)
    assert contract_info.is_deleted is True, "Contract should be deleted"

    transfer_contract_info = ContractInfoQuery(transfer_contract_id).execute(env.client)
    assert (
        transfer_contract_info.contract_id == transfer_contract_id
    ), "Contract ID should match"
    assert (
        transfer_contract_info.balance == Hbar(2).to_tinybars()
    ), "Contract balance should be 2 HBAR"


@pytest.mark.integration
def test_integration_contract_delete_transaction_fails_when_deleted_twice(env):
    """Test that deleting a contract twice fails."""
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_contract_memo("some test contract create transaction memo")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Delete once
    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract deletion failed with status: {ResponseCode(receipt.status).name}"

    # Try to delete again
    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.CONTRACT_DELETED, (
        f"Contract deletion should have failed with CONTRACT_DELETED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_delete_transaction_fails_when_contract_does_not_exist(
    env,
):
    """Test that deleting a non-existing contract fails."""
    # Create a contract ID that doesn't exist on the network
    contract_id = ContractId(0, 0, 999999999)

    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.INVALID_CONTRACT_ID, (
        f"Contract deletion should have failed with INVALID_CONTRACT_ID status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_delete_transaction_fails_with_obtainer_required(env):
    """Test that contract deletion fails if no transfer account or contract is set."""
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("test contract delete transaction")
        .set_initial_balance(Hbar(1).to_tinybars())
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Attempt to delete without setting transfer_account_id or transfer_contract_id
    with pytest.raises(
        PrecheckError, match="failed precheck with status: OBTAINER_REQUIRED"
    ):
        ContractDeleteTransaction().set_contract_id(contract_id).execute(env.client)


@pytest.mark.integration
def test_integration_contract_delete_transaction_fails_with_immutable_contract(env):
    """Test that contract deletion fails if the contract is immutable."""
    # Create a contract without admin key to make it immutable
    # This prevents the contract from being deleted later
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("test contract delete transaction")
        .set_initial_balance(Hbar(1).to_tinybars())
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.MODIFYING_IMMUTABLE_CONTRACT, (
        f"Contract deletion should have failed with MODIFYING_IMMUTABLE_CONTRACT status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_delete_transaction_fails_with_invalid_signature(env):
    """Test that contract deletion fails if the signature is invalid."""
    admin_private_key = PrivateKey.generate_ed25519()

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(admin_private_key.public_key())
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_contract_memo("test contract delete transaction")
        .set_initial_balance(Hbar(1).to_tinybars())
        .freeze_with(env.client)
        .sign(admin_private_key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Try to delete without signing with the admin key
    receipt = (
        ContractDeleteTransaction()
        .set_contract_id(contract_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Contract deletion should have failed with INVALID_SIGNATURE status but got: "
        f"{ResponseCode(receipt.status).name}"
    )
