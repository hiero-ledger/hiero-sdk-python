"""Integration tests for TransactionRecordQuery end-to-end functionality."""

import os

import pytest

from hiero_sdk_python import AccountId, TransactionRecord
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import (
    TokenAssociateTransaction,
)
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils import IntegrationTestEnv, create_fungible_token, create_nft_token


def _submit_alias_auto_create_transfer(env: IntegrationTestEnv):
    """Submit a transfer to an EVM alias to trigger child auto-account creation."""
    alias_key = PrivateKey.generate_ecdsa()
    alias_account_id = AccountId.from_evm_address(alias_key.public_key().to_evm_address(), 0, 0)

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(alias_account_id, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(-1).to_tinybars())
    )
    receipt = transaction.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS

    return transaction.transaction_id


@pytest.mark.integration
def test_transaction_record_query_can_execute():
    """Test that a basic transaction record query can execute successfully."""
    env = IntegrationTestEnv()

    try:
        # Generate new key
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()

        # Create new account
        receipt = (
            AccountCreateTransaction()
            .set_key_without_alias(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, "Account creation failed"

        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()


@pytest.mark.integration
def test_transaction_record_query_include_children_returns_child_records():
    """Querying an alias auto-create parent record should return parsed child records."""
    env = IntegrationTestEnv()
    try:
        parent_transaction_id = _submit_alias_auto_create_transfer(env)
        parent_account_id = parent_transaction_id.account_id

        parent_record = (
            TransactionRecordQuery()
            .set_transaction_id(parent_transaction_id)
            .set_include_children(True)
            .execute(env.client)
        )

        assert parent_record.transaction_id == parent_transaction_id
        assert parent_record.receipt.status == ResponseCode.SUCCESS
        assert len(parent_record.children) > 0
        assert parent_record.transfers[parent_account_id] < 0

        child_record = parent_record.children[0]
        created_account_id = child_record.receipt.account_id

        assert isinstance(child_record, TransactionRecord)
        assert child_record.receipt.status == ResponseCode.SUCCESS
        assert child_record.transaction_id == parent_transaction_id
        assert created_account_id is not None
        assert created_account_id.shard == 0
        assert created_account_id.realm == 0
        assert created_account_id.num > 0
        assert child_record.transaction_hash != parent_record.transaction_hash
        assert child_record.transaction_memo == ""
        assert child_record.children == []
        assert child_record.duplicates == []
    finally:
        env.close()


@pytest.mark.integration
def test_transaction_record_query_can_execute_nft_transfer():
    """Test that NFT transfers are correctly captured in the transaction record."""
    env = IntegrationTestEnv()

    try:
        new_account = env.create_account()

        token_id = create_nft_token(env)

        # Mint NFTs
        receipt = TokenMintTransaction().set_token_id(token_id).set_metadata([b"NFT 1", b"NFT 2"]).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, (
            f"NFT mint failed with status: {ResponseCode(receipt.status).name}"
        )
        serial_numbers = receipt.serial_numbers

        assert len(serial_numbers) == 2, "Expected two NFTs to be minted"

        # Associate token with new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )

        # Transfer NFTs
        receipt = (
            TransferTransaction()
            .add_nft_transfer(NftId(token_id, serial_numbers[0]), env.operator_id, new_account.id)
            .add_nft_transfer(NftId(token_id, serial_numbers[1]), env.operator_id, new_account.id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, (
            f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        )

        # Query the record
        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

        # Verify NFT transfers
        assert len(record.nft_transfers) == 1
        assert len(record.nft_transfers[token_id]) == 2, "Expected two NFT transfers in the record"
        for i, transfer in enumerate(record.nft_transfers[token_id]):
            assert transfer.sender_id == env.operator_id, "Sender should be the operator account"
            assert transfer.receiver_id == new_account.id, "Receiver should be the new account"
            assert transfer.serial_number == serial_numbers[i], "Serial number should match the minted NFT"

        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()


@pytest.mark.integration
def test_transaction_record_query_can_execute_fungible_transfer():
    """Test that fungible token transfers are correctly captured in the record."""
    env = IntegrationTestEnv()

    try:
        new_account = env.create_account()

        token_id = create_fungible_token(env)

        # Associate token with new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, (
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )

        # Transfer tokens
        transfer_amount = 1000
        receipt = (
            TransferTransaction()
            .add_token_transfer(token_id, env.operator_id, -transfer_amount)
            .add_token_transfer(token_id, new_account.id, transfer_amount)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, (
            f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        )

        # Query the record
        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

        # Verify token transfers
        assert len(record.token_transfers) == 1
        assert record.token_transfers[token_id][env.operator_id] == -transfer_amount, "Operator should have sent tokens"
        assert record.token_transfers[token_id][new_account.id] == transfer_amount, (
            "New account should have received tokens"
        )

        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("HIERO_RUN_FLAKY_TESTS", "0").lower() not in ("1", "true", "yes"),
    reason=(
        "Flaky: Duplicate record creation depends on race-condition timing before consensus. "
        "Often no duplicates are created due to network/node scheduling. "
        "Set HIERO_RUN_FLAKY_TESTS=1 to run this test manually/locally."
    ),
)
def test_query_with_include_duplicates():
    """Verify that duplicate records are returned when the flag is enabled."""
    env = IntegrationTestEnv()
    try:
        # Use a fresh keypair for isolation
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()

        # Build and sign the transaction **once** (important: same sigs + same tx_id for duplicates)
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(new_account_public_key)
            .set_initial_balance(Hbar.from_tinybars(10_000_000))  # 0.1 HBAR
        )

        # Freeze and sign (this sets the tx_id based on payer/validStart)
        tx.freeze_with(env.client)
        tx.sign(env.operator_key)  # assuming env has operator key for payer

        # Step 1: Submit once → success
        receipt = tx.execute(env.client)
        tx_id = receipt.transaction_id  # or tx.transaction_id

        assert receipt.status == ResponseCode.SUCCESS  # or equivalent enum

        # Step 2: Submit the **same tx object** again → should be duplicate
        duplicate_receipt = tx.execute(env.client)

        # On testnet/local, this should be DUPLICATE_TRANSACTION
        assert duplicate_receipt.status in (
            ResponseCode.DUPLICATE_TRANSACTION,
            ResponseCode.SUCCESS,
        )  # sometimes timing allows second to win

        # Optional: submit a third time for more duplicates
        tx.execute(env.client)  # ignore receipt

        # Give the network a moment to process (usually fast, but helps reliability)
        # import time; time.sleep(1)  # if needed on slow networks

        # Step 3: Query with include_duplicates=True
        record = TransactionRecordQuery().set_transaction_id(tx_id).set_include_duplicates(True).execute(env.client)

        # Core assertions for the feature
        assert record.transaction_id == tx_id
        assert len(record.duplicates) >= 2, (
            f"Expected at least 2 duplicates after 3 submissions, got {len(record.duplicates)}"
        )

        # Verify duplicates are TransactionRecord instances
        if record.duplicates:
            assert isinstance(record.duplicates[0], TransactionRecord)
            # Verify duplicate has expected fields populated
            for dup in record.duplicates:
                assert dup.receipt is not None, "Duplicate record should have receipt"

        # If you submitted 3 times, expect >=2 duplicates, etc.
        # print(f"Found {len(record.duplicates)} duplicates")  # for debug
    finally:
        env.close()


@pytest.mark.integration
def test_transaction_record_new_fields():
    """Simple test to verify some fields in TransactionRecord.

    consensus_timestamp, automatic_token_associations, paid_staking_rewards,
    evm_address, alias, ethereum_hash, parent_consensus_timestamp,
    assessed_custom_fees, schedule_ref, and PRNG oneof handling.
    """
    env = IntegrationTestEnv()
    try:
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()

        receipt = (
            AccountCreateTransaction()
            .set_key_without_alias(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS

        record: TransactionRecord = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

        _assert_basic_record_fields(record, receipt)
        _assert_fields(record)
    finally:
        env.close()


def _assert_basic_record_fields(record: TransactionRecord, receipt) -> None:
    """Assert basic fields that existed before this PR."""
    assert record.transaction_id == receipt.transaction_id
    assert record.transaction_fee > 0
    assert record.consensus_timestamp is not None
    assert record.transaction_hash is not None and len(record.transaction_hash) > 0


def _assert_fields(record: TransactionRecord) -> None:
    """Assert all newly exposed fields from this PR."""
    _assert_list_fields(record)
    _assert_optional_bytes_fields(record)
    _assert_timestamp_and_schedule_fields(record)
    _assert_prng_fields(record)
    _assert_token_associations(record)


def _assert_list_fields(record: TransactionRecord) -> None:
    """Assert list fields are properly initialized."""
    assert isinstance(record.automatic_token_associations, list)
    assert isinstance(record.paid_staking_rewards, list)
    assert isinstance(record.assessed_custom_fees, list)


def _assert_optional_bytes_fields(record: TransactionRecord) -> None:
    """Assert optional bytes fields."""
    assert record.evm_address is None or isinstance(record.evm_address, bytes)
    assert record.alias is None or isinstance(record.alias, bytes)
    assert record.ethereum_hash is None or isinstance(record.ethereum_hash, bytes)


def _assert_timestamp_and_schedule_fields(record: TransactionRecord) -> None:
    """Assert timestamp and schedule related fields."""
    assert record.parent_consensus_timestamp is None or isinstance(record.parent_consensus_timestamp, Timestamp)
    assert record.schedule_ref is None or isinstance(record.schedule_ref, ScheduleId)


def _assert_prng_fields(record: TransactionRecord) -> None:
    """Assert PRNG oneof handling."""
    assert not (record.prng_number is not None and record.prng_bytes is not None), (
        "prng_number and prng_bytes are mutually exclusive"
    )

    if record.prng_number is not None:
        assert isinstance(record.prng_number, int)
    if record.prng_bytes is not None:
        assert isinstance(record.prng_bytes, bytes)


def _assert_token_associations(record: TransactionRecord) -> None:
    """Assert TokenAssociation model fields."""
    for assoc in record.automatic_token_associations:
        assert hasattr(assoc, "token_id")
        assert hasattr(assoc, "account_id")
