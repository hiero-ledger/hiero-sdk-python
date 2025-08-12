"""
Integration tests for the AccountUpdateTransaction class.
"""

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_account_update_transaction_can_execute(env):
    """Test that the AccountUpdateTransaction can be executed successfully."""
    # Create initial account
    initial_memo = "Initial account memo"

    receipt = (
        AccountCreateTransaction()
        .set_key(env.operator_key.public_key())
        .set_initial_balance(Hbar(2))
        .set_account_memo(initial_memo)
        .set_receiver_signature_required(False)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    # Generate new key for update
    new_private_key = PrivateKey.generate_ed25519()
    new_public_key = new_private_key.public_key()
    new_memo = "Updated account memo"
    new_auto_renew_period = Duration(8000000)  # ~93 days

    # Update account with new key, memo, and other fields
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_key(new_public_key)
        .set_account_memo(new_memo)
        .set_receiver_signature_required(True)
        .set_auto_renew_period(new_auto_renew_period)
        .freeze_with(env.client)
        .sign(new_private_key)  # Sign with new key
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account update failed with status: {ResponseCode(receipt.status).name}"

    # Query account info to verify updates
    info = AccountInfoQuery(account_id).execute(env.client)
    assert str(info.account_id) == str(account_id), "Account ID should match"
    assert (
        info.key.to_bytes_raw() == new_public_key.to_bytes_raw()
    ), "Public key should be updated"
    assert info.account_memo == new_memo, "Account memo should be updated"
    assert (
        info.receiver_signature_required is True
    ), "Receiver signature requirement should be updated"
    assert (
        info.auto_renew_period == new_auto_renew_period
    ), "Auto renew period should be updated"


@pytest.mark.integration
def test_integration_account_update_transaction_fails_with_invalid_account_id(env):
    """Test that AccountUpdateTransaction fails with an invalid account ID."""
    # Create an account ID that doesn't exist on the network
    invalid_account_id = AccountId(0, 0, 999999999)

    receipt = (
        AccountUpdateTransaction()
        .set_account_id(invalid_account_id)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.INVALID_ACCOUNT_ID, (
        f"Account update should have failed with status INVALID_ACCOUNT_ID, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_update_transaction_fails_with_invalid_signature(env):
    """Test that AccountUpdateTransaction fails when not signed with the correct key."""
    # Create initial account
    initial_private_key = PrivateKey.generate_ed25519()
    initial_public_key = initial_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(initial_public_key)
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    # Try to update without signing with the account's key
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_account_memo("New memo")
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Account update should have failed with status INVALID_SIGNATURE, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_update_transaction_partial_update(env):
    """Test that AccountUpdateTransaction can update only specific fields."""
    # Create initial account
    receipt = (
        AccountCreateTransaction()
        .set_key(env.operator_key.public_key())
        .set_initial_balance(Hbar(1))
        .set_account_memo("Initial memo")
        .set_receiver_signature_required(False)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    # Update only the memo, leaving other fields unchanged
    new_memo = "Only memo updated"
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_account_memo(new_memo)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account update failed with status: {ResponseCode(receipt.status).name}"

    # Query account info to verify only memo was updated
    info = AccountInfoQuery(account_id).execute(env.client)

    assert str(info.account_id) == str(account_id), "Account ID should match"
    assert (
        info.key.to_bytes_raw() == env.operator_key.public_key().to_bytes_raw()
    ), "Public key should remain unchanged"
    assert info.account_memo == new_memo, "Account memo should be updated"
    assert (
        info.receiver_signature_required is False
    ), "Receiver signature requirement should remain unchanged"


@pytest.mark.integration
def test_integration_account_update_transaction_invalid_auto_renew_period(env):
    """Test that AccountUpdateTransaction fails with invalid auto renew period."""
    # Create initial account
    receipt = (
        AccountCreateTransaction()
        .set_key(env.operator_key.public_key())
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    # Try to update with invalid auto renew period
    invalid_period = Duration(777600000)  # 9000 days
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_auto_renew_period(invalid_period)
        .execute(env.client)
    )

    # Should fail with AUTORENEW_DURATION_NOT_IN_RANGE
    assert receipt.status == ResponseCode.AUTORENEW_DURATION_NOT_IN_RANGE, (
        f"Account update should have failed with status AUTORENEW_DURATION_NOT_IN_RANGE, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_update_transaction_insufficient_fee_large_expiration(env):
    """Test that AccountUpdateTransaction fails with insufficient fee for large expiration time."""
    # Create initial account
    receipt = (
        AccountCreateTransaction()
        .set_key(env.operator_key.public_key())
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    # Try to update with a very large expiration time that would require higher fees
    large_expiration = Timestamp(seconds=int(1e11), nanos=0)
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_expiration_time(large_expiration)
        .execute(env.client)
    )

    # Should fail with INSUFFICIENT_TX_FEE
    assert receipt.status == ResponseCode.INSUFFICIENT_TX_FEE, (
        f"Account update should have failed with status INSUFFICIENT_TX_FEE, "
        f"but got {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_update_transaction_with_only_account_id(env):
    """Test that AccountUpdateTransaction can execute with only account ID set."""
    # Create initial account
    receipt = (
        AccountCreateTransaction()
        .set_key(env.operator_key.public_key())
        .set_initial_balance(Hbar(1))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

    account_id = receipt.account_id
    assert account_id is not None, "Account ID should not be None"

    receipt = AccountUpdateTransaction().set_account_id(account_id).execute(env.client)

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Account update failed with status: {ResponseCode(receipt.status).name}"
