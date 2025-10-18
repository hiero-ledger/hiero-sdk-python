"""
Integration tests for Account Allowance functionality.
"""

import pytest

from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_allowance_delete_transaction import (
    AccountAllowanceDeleteTransaction,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import create_fungible_token, create_nft_token, env


def _create_spender_and_receiver_accounts(env):
    """Helper function to create spender and receiver accounts"""
    spender_account = env.create_account()
    receiver_account = env.create_account()

    return spender_account, receiver_account


def _associate_token_with_account(env, account, token_id):
    """Helper function to associate token with account"""
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account.id)
        .add_token_id(token_id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token association failed with status: {ResponseCode(receipt.status).name}"


def _mint_nft(env, token_id, metadata):
    """Helper function to mint NFT"""
    receipt = (
        TokenMintTransaction().set_token_id(token_id).set_metadata(metadata).execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"NFT mint failed with status: {ResponseCode(receipt.status).name}"
    assert len(receipt.serial_numbers) > 0

    nft_ids = []
    for serial_number in receipt.serial_numbers:
        nft_ids.append(NftId(token_id, serial_number))

    return nft_ids


@pytest.mark.integration
def test_integration_cannot_transfer_on_behalf_of_spender_without_allowance_approval(env):
    """Test that a spender cannot transfer NFTs on behalf of account without allowance approval."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    token_id = create_nft_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    # Mint NFT to operator account
    nft_ids = _mint_nft(env, token_id, [b"\x01"])
    nft_id = nft_ids[0]

    # Try to transfer NFT on behalf of operator without allowance approval
    # This should fail because the spender doesn't have allowance to transfer on behalf of operator
    transfer_receipt = (
        TransferTransaction()
        .add_approved_nft_transfer(nft_id, env.operator_id, receiver_account.id)
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )

    # Verify the transaction failed with the expected error
    assert transfer_receipt.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"Transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(transfer_receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_can_transfer_on_behalf_of_spender_with_allowance_approval(env):
    """Test that a spender can transfer NFTs on behalf of account with allowance approval."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    # Create NFT token
    token_id = create_nft_token(env)
    assert token_id is not None

    # Associate token with receiver account
    _associate_token_with_account(env, receiver_account, token_id)

    nft_ids = _mint_nft(env, token_id, [b"\x01"])

    nft_id = nft_ids[0]

    # Approve allowance for spender to transfer NFT on behalf of operator
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance(
            nft_id=nft_id,
            owner_account_id=env.operator_id,
            spender_account_id=spender_account.id,
        )
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Allowance approval failed with status: {ResponseCode(receipt.status).name}"

    transaction_id = TransactionId.generate(spender_account.id)
    # Now transfer NFT on behalf of operator with allowance approval
    receipt = (
        TransferTransaction()
        .set_transaction_id(transaction_id)
        .add_approved_nft_transfer(
            nft_id=nft_id,
            sender_id=env.operator_id,
            receiver_id=receiver_account.id,
        )
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(receipt.status).name}"


@pytest.mark.integration
def test_integration_hbar_allowance(env):
    """Test HBAR allowance approval and deletion functionality."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_hbar_allowance(env.operator_id, spender_account.id, Hbar(4))
        .execute(env.client)
    )  # Approve HBAR allowance for spender

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"HBAR allowance approval failed with status: {ResponseCode(receipt.status).name}"

    # Set operator to spender account
    env.client.set_operator(spender_account.id, spender_account.key)

    # Transfer HBAR on behalf of operator using allowance
    receipt = (
        TransferTransaction()
        .add_approved_hbar_transfer(env.operator_id, -Hbar(2).to_tinybars())
        .add_approved_hbar_transfer(receiver_account.id, Hbar(2).to_tinybars())
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"HBAR transfer failed with status: {ResponseCode(receipt.status).name}"

    # Reset operator back to original
    env.client.set_operator(env.operator_id, env.operator_key)

    # Delete allowance
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_hbar_allowance(env.operator_id, spender_account.id, Hbar(0))
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"HBAR allowance deletion failed with status: {ResponseCode(receipt.status).name}"

    # Set operator to spender account
    env.client.set_operator(spender_account.id, spender_account.key)

    receipt = (
        TransferTransaction()
        .add_approved_hbar_transfer(env.operator_id, -Hbar(2).to_tinybars())
        .add_approved_hbar_transfer(receiver_account.id, Hbar(2).to_tinybars())
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"HBAR transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_fungible_token_allowance(env):
    """Test fungible token allowance approval and deletion functionality."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    # Create fungible token
    token_id = create_fungible_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    # Approve fungible token allowance for spender
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_allowance(token_id, env.operator_id, spender_account.id, 20)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token allowance approval failed with status: {ResponseCode(receipt.status).name}"

    env.client.set_operator(spender_account.id, spender_account.key)  # Set operator to spender

    # Transfer fungible token on behalf of operator using allowance
    receipt = (
        TransferTransaction()
        .add_approved_token_transfer(token_id, env.operator_id, -10)
        .add_approved_token_transfer(token_id, receiver_account.id, 10)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token transfer failed with status: {ResponseCode(receipt.status).name}"

    env.client.set_operator(env.operator_id, env.operator_key)  # Reset operator

    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_allowance(token_id, env.operator_id, spender_account.id, 0)
        .execute(env.client)
    )  # Delete allowance
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token allowance deletion failed with status: {ResponseCode(receipt.status).name}"

    # Set operator to spender account
    env.client.set_operator(spender_account.id, spender_account.key)

    # Transfer HBAR on behalf of operator using allowance
    receipt = (
        TransferTransaction()
        .add_approved_token_transfer(token_id, env.operator_id, -10)
        .add_approved_token_transfer(token_id, receiver_account.id, 10)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"Token transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_cant_transfer_on_behalf_of_spender_after_removing_the_allowance_approval(env):
    """Test that a spender cannot transfer NFTs after the allowance approval is removed."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    token_id = create_nft_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    nft_ids = _mint_nft(env, token_id, [b"\x01", b"\x02"])
    nft1 = nft_ids[0]
    nft2 = nft_ids[1]

    approve_receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance(nft1, env.operator_id, spender_account.id)
        .approve_token_nft_allowance(nft2, env.operator_id, spender_account.id)
        .execute(env.client)
    )  # Approve allowance for both NFTs
    assert (
        approve_receipt.status == ResponseCode.SUCCESS
    ), f"Allowance approval failed with status: {ResponseCode(approve_receipt.status).name}"

    delete_receipt = (
        AccountAllowanceDeleteTransaction()
        .delete_all_token_nft_allowances(nft2, env.operator_id)
        .execute(env.client)
    )  # Delete allowance for nft2
    assert (
        delete_receipt.status == ResponseCode.SUCCESS
    ), f"Allowance deletion failed with status: {ResponseCode(delete_receipt.status).name}"

    # Transfer nft1 (should succeed - allowance still exists)
    transfer_receipt = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(spender_account.id))
        .add_approved_nft_transfer(nft1, env.operator_id, receiver_account.id)
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )
    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    # Transfer nft2 (should fail - allowance was deleted)
    transfer_receipt2 = (
        TransferTransaction()
        .add_approved_nft_transfer(nft2, env.operator_id, receiver_account.id)
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )
    assert transfer_receipt2.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"Transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(transfer_receipt2.status).name}"
    )


@pytest.mark.integration
def test_integration_cant_remove_serial_allowance_when_all_serials_allowed(env):
    """Test that single serial number allowance can't be removed when allowance for all serials."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    token_id = create_nft_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    nft_ids = _mint_nft(env, token_id, [b"\x01", b"\x02"])
    nft1 = nft_ids[0]
    nft2 = nft_ids[1]

    approve_receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(token_id, env.operator_id, spender_account.id)
        .execute(env.client)
    )  # Approve allowance for all serials
    assert (
        approve_receipt.status == ResponseCode.SUCCESS
    ), f"Allowance approval failed with status: {ResponseCode(approve_receipt.status).name}"

    # Transfer nft1 (should succeed - all serials allowed)
    tx = TransferTransaction()
    tx.transaction_id = TransactionId.generate(spender_account.id)
    transfer_receipt = (
        tx.add_nft_transfer(nft1, env.operator_id, receiver_account.id, is_approved=True)
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )
    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    # Try to delete allowance for nft2 (should not affect the all-serial allowance)
    delete_receipt = (
        AccountAllowanceDeleteTransaction()
        .delete_all_token_nft_allowances(nft2, env.operator_id)
        .execute(env.client)
    )
    assert (
        delete_receipt.status == ResponseCode.SUCCESS
    ), f"Allowance deletion failed with status: {ResponseCode(delete_receipt.status).name}"

    # Transfer nft2 (should still succeed - all serials allowance still active)
    tx = TransferTransaction()
    tx.transaction_id = TransactionId.generate(spender_account.id)
    transfer_receipt2 = (
        tx.add_nft_transfer(nft2, env.operator_id, receiver_account.id, is_approved=True)
        .freeze_with(env.client)
        .sign(spender_account.key)
        .execute(env.client)
    )
    assert (
        transfer_receipt2.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt2.status).name}"


@pytest.mark.integration
def test_integration_can_delegate_single_nft_after_all_serials_allowance(env):
    """Test that an account with all-serials allowance can delegate individual NFTs."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    delegate_spender_account = env.create_account()  # Create delegate spender account

    token_id = create_nft_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    nft_ids = _mint_nft(env, token_id, [b"\x01", b"\x02"])
    nft1 = nft_ids[0]
    nft2 = nft_ids[1]

    approve_receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(token_id, env.operator_id, spender_account.id)
        .execute(env.client)
    )  # Approve allowance for all serials to spender
    assert (
        approve_receipt.status == ResponseCode.SUCCESS
    ), f"Allowance approval failed with status: {ResponseCode(approve_receipt.status).name}"

    env.client.set_operator(spender_account.id, spender_account.key)  # Set spender as operator

    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_with_delegating_spender(
            nft1, env.operator_id, delegate_spender_account.id, spender_account.id
        )
        .execute(env.client)
    )  # Approve delegation of nft1 to delegate spender
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Delegate allowance approval failed with status: {ResponseCode(receipt.status).name}"

    env.client.set_operator(delegate_spender_account.id, delegate_spender_account.key)

    # Transfer nft1 using delegate spender (should succeed)
    transfer_receipt = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(delegate_spender_account.id))
        .add_approved_nft_transfer(nft1, env.operator_id, receiver_account.id)
        .execute(env.client)
    )
    assert (
        transfer_receipt.status == ResponseCode.SUCCESS
    ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    # Transfer nft2 using delegate spender (should fail - no delegation for nft2)
    transfer_receipt2 = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(delegate_spender_account.id))
        .add_approved_nft_transfer(nft2, env.operator_id, receiver_account.id)
        .execute(env.client)
    )
    assert transfer_receipt2.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"Transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(transfer_receipt2.status).name}"
    )


@pytest.mark.integration
def test_integration_cannot_send_deleted_token_nft_serials(env):
    """Test that you cannot send NFTs if the token NFT serials are deleted from allowance."""
    spender_account, receiver_account = _create_spender_and_receiver_accounts(env)

    token_id = create_nft_token(env)
    assert token_id is not None

    _associate_token_with_account(env, receiver_account, token_id)

    nft_ids = _mint_nft(env, token_id, [b"\x01"])
    nft = nft_ids[0]

    # Approve allowance for all serials
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(token_id, env.operator_id, spender_account.id)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Allowance approval failed with status: {ResponseCode(receipt.status).name}"

    # Delete the allowance for all serials
    receipt = (
        AccountAllowanceApproveTransaction()
        .delete_token_nft_allowance_all_serials(token_id, env.operator_id, spender_account.id)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Allowance deletion failed with status: {ResponseCode(receipt.status).name}"

    env.client.set_operator(spender_account.id, spender_account.key)  # Set spender as operator

    # Try to transfer nft (should fail - allowance was deleted)
    transfer_receipt = (
        TransferTransaction()
        .add_approved_nft_transfer(nft, env.operator_id, receiver_account.id)
        .execute(env.client)
    )
    assert transfer_receipt.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE, (
        f"Transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE"
        f"status but got: {ResponseCode(transfer_receipt.status).name}"
    )
