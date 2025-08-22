"""
Integration tests for AccountDeleteTransaction.
"""

import pytest

from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from tests.integration.utils_for_test import (
    create_fungible_token,
    create_nft_token,
    env,
)


@pytest.mark.integration
def test_integration_account_delete_transaction_can_execute(env):
    """Test that the AccountDeleteTransaction can execute."""
    account = env.create_account()
    transfer_account = env.create_account()

    receipt = (
        AccountDeleteTransaction()
        .set_transfer_account_id(transfer_account.id)
        .set_account_id(account.id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Delete account failed with status: {ResponseCode(receipt.status).name}"

    transfer_account_info = AccountInfoQuery(transfer_account.id).execute(env.client)
    assert (
        transfer_account_info.account_id == transfer_account.id
    ), "Account ID should match"
    assert (
        transfer_account_info.balance.to_tinybars() == Hbar(2).to_tinybars()
    ), f"Account balance should be 2 HBAR but got {transfer_account_info.balance.to_tinybars()}"


@pytest.mark.integration
def test_integration_account_delete_transaction_fails_with_invalid_account_id(env):
    """Test that AccountDeleteTransaction fails if account_id is invalid."""
    account_id = AccountId(0, 0, 999999999)

    receipt = (
        AccountDeleteTransaction()
        .set_account_id(account_id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_ACCOUNT_ID, (
        f"Delete account should have failed with INVALID_ACCOUNT_ID status"
        f" but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_delete_transaction_fails_with_no_signature(env):
    """Test that AccountDeleteTransaction fails if not signed by the account's key."""
    account = env.create_account()

    receipt = (
        AccountDeleteTransaction()
        .set_account_id(account.id)
        .set_transfer_account_id(env.operator_id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Delete account should have failed with INVALID_SIGNATURE"
        f" but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_delete_transaction_fails_with_pending_airdrops(env):
    """Test that AccountDeleteTransaction fails if the account has pending airdrops."""
    # Create fungible token and NFT
    token_id = create_fungible_token(env)
    nft_id = create_nft_token(env)

    # Mint two NFTs
    nft_metadata = [b"nft1", b"nft2"]
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_id)
        .set_metadata(nft_metadata)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token mint failed: {ResponseCode(receipt.status).name}"
    nft_serials = receipt.serial_numbers
    assert len(nft_serials) == 2, "Should have minted 2 NFTs"

    # Create receiver account
    receiver = env.create_account()

    # Airdrop: transfer 2 NFTs and 100 FT to receiver, -100 FT from operator
    receipt = (
        TokenAirdropTransaction()
        .add_nft_transfer(NftId(nft_id, nft_serials[0]), env.operator_id, receiver.id)
        .add_nft_transfer(NftId(nft_id, nft_serials[1]), env.operator_id, receiver.id)
        .add_token_transfer(token_id, receiver.id, 100)
        .add_token_transfer(token_id, env.operator_id, -100)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Token airdrop failed: {ResponseCode(receipt.status).name}"

    record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
    assert len(record.new_pending_airdrops) == 3, "Should have 3 pending airdrops"

    # Attempt to delete the sender (operator) account
    receipt = (
        AccountDeleteTransaction()
        .set_account_id(env.operator_id)
        .set_transfer_account_id(receiver.id)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.ACCOUNT_HAS_PENDING_AIRDROPS, (
        f"Delete account should have failed with ACCOUNT_HAS_PENDING_AIRDROPS"
        f"but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_account_delete_transaction_fails_when_deleted_twice(env):
    """Test that deleting an account twice fails."""
    account = env.create_account()
    transfer_account = env.create_account()

    receipt = (
        AccountDeleteTransaction()
        .set_account_id(account.id)
        .set_transfer_account_id(transfer_account.id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"First account deletion failed with status: {ResponseCode(receipt.status).name}"

    receipt = (
        AccountDeleteTransaction()
        .set_account_id(account.id)
        .set_transfer_account_id(transfer_account.id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.ACCOUNT_DELETED, (
        f"Second account deletion should have failed with ACCOUNT_DELETED status"
        f" but got: {ResponseCode(receipt.status).name}"
    )
