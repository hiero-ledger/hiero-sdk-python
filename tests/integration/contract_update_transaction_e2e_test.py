"""
Integration tests for the ContractUpdateTransaction class.
"""

import datetime

import pytest

from examples.contracts import CONTRACT_DEPLOY_GAS, SIMPLE_CONTRACT_BYTECODE
from hiero_sdk_python import Duration
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_contract_update_transaction_can_execute(env):
    """Test that a contract can be updated successfully."""
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_max_automatic_token_associations(1)
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_contract_memo("[e2e::ContractCreateTransaction]")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    current_time = datetime.datetime.now(datetime.timezone.utc)
    future_expiration = Timestamp.from_date(current_time + datetime.timedelta(days=92))
    updated_memo = "[e2e::ContractUpdateTransaction]"
    updated_duration = Duration(7948800)
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_contract_memo(updated_memo)
        .set_auto_renew_account_id(env.operator_id)
        .set_auto_renew_period(updated_duration)
        .set_max_automatic_token_associations(10)
        .set_expiration_time(future_expiration)
        .execute(env.client)
    )
    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"

    info = ContractInfoQuery().set_contract_id(contract_id).execute(env.client)
    assert info.contract_id == contract_id, "Contract ID should be updated"
    assert (
        info.admin_key.to_bytes_raw() == env.operator_key.public_key().to_bytes_raw()
    ), "Admin key should be unchanged"
    assert info.contract_memo == updated_memo, "Contract memo should be updated"
    assert (
        info.auto_renew_account_id == env.operator_id
    ), "Auto renew account ID should be updated"
    assert (
        info.auto_renew_period == updated_duration
    ), "Auto renew period should be updated"
    assert (
        info.max_automatic_token_associations == 10
    ), "Max automatic token associations should be updated"
    assert (
        info.expiration_time.seconds == future_expiration.seconds
    ), "Expiration time should be updated"


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
    new_admin_key = PrivateKey.generate_ed25519()

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_max_automatic_token_associations(10)
        .set_contract_memo("[e2e::ContractCreateTransaction]")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(new_admin_key.public_key())
        .freeze_with(env.client)
        .sign(new_admin_key)
        .execute(env.client)
    )
    assert (
        update_receipt.status == ResponseCode.SUCCESS
    ), f"Contract update failed with status: {ResponseCode(update_receipt.status).name}"

    contract_info = ContractInfoQuery().set_contract_id(contract_id).execute(env.client)
    assert (
        contract_info.admin_key.to_string() == new_admin_key.public_key().to_string()
    ), "Admin key should be updated"
    assert (
        contract_info.contract_memo == "[e2e::ContractCreateTransaction]"
    ), "Auto renew account ID should be unchanged"
    assert (
        contract_info.max_automatic_token_associations == 10
    ), "Max automatic token associations should be unchanged"


@pytest.mark.integration
def test_integration_contract_update_transaction_invalid_auto_renew_period(env):
    """Test that ContractUpdateTransaction fails with invalid auto renew period."""
    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_max_automatic_token_associations(10)
        .set_contract_memo("[e2e::ContractCreateTransaction]")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Try to update with invalid auto renew period
    invalid_period = Duration(777600000)  # 9000 days
    receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_auto_renew_period(invalid_period)
        .execute(env.client)
    )

    # Should fail with AUTORENEW_DURATION_NOT_IN_RANGE
    assert receipt.status == ResponseCode.AUTORENEW_DURATION_NOT_IN_RANGE, (
        f"Contract update should have failed with status AUTORENEW_DURATION_NOT_IN_RANGE, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_contract_update_transaction_fails_with_invalid_signature(env):
    """Test that ContractUpdateTransaction fails when not signed with the new admin key."""
    new_admin_key = PrivateKey.generate_ed25519()

    contract_receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytes.fromhex(SIMPLE_CONTRACT_BYTECODE))
        .set_max_automatic_token_associations(1)
        .set_contract_memo("[e2e::ContractCreateTransaction]")
        .execute(env.client)
    )
    assert (
        contract_receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(contract_receipt.status).name}"

    contract_id = contract_receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    # Attempt to update the contract without signing with the new admin key
    update_receipt = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(new_admin_key.public_key())
        .set_contract_memo("[e2e::ContractUpdateTransaction]")
        .execute(env.client)
    )

    assert update_receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Contract update should have failed with status INVALID_SIGNATURE, "
        f"but got {ResponseCode(update_receipt.status).name}"
    )
