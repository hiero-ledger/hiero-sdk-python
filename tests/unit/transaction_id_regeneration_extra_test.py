"""Extra tests for transaction ID regeneration (PR #2657 review feedback)."""

from __future__ import annotations

import copy
import pickle
from unittest.mock import patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def _expired():
    return transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.TRANSACTION_EXPIRED)


def test_user_set_transaction_id_is_not_regenerated():
    """Test that a transaction ID supplied by the caller is never replaced on expiry."""
    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        user_transaction_id = TransactionId.generate(client.operator_account_id)
        transaction = (
            TransferTransaction()
            .add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))
            .set_transaction_id(user_transaction_id)
        )

        with pytest.raises(PrecheckError):
            transaction.execute(client)

        assert transaction.transaction_id == user_transaction_id


def test_user_set_transaction_id_is_not_regenerated_for_chunked_transaction(topic_id):
    """Test that a caller-supplied ID on a chunked transaction is not replaced on expiry."""
    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        user_transaction_id = TransactionId.generate(client.operator_account_id)
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message("ABCD")
            .set_chunk_size(1)
            .set_transaction_id(user_transaction_id)
        )
        tx.freeze_with(client)
        original_ids = list(tx._transaction_ids)

        with pytest.raises(PrecheckError):
            tx.execute_all(client)

        assert list(tx._transaction_ids) == original_ids
        assert tx._initial_transaction_id == user_transaction_id


def test_transaction_supports_deepcopy_and_pickle():
    """Test that the execution lock does not break copy.deepcopy() or pickle."""
    transaction = TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))

    for clone in (copy.deepcopy(transaction), pickle.loads(pickle.dumps(transaction))):
        assert clone._execution_lock is not transaction._execution_lock
        assert clone._execution_lock.acquire(blocking=False)
        clone._execution_lock.release()


def test_frozen_transaction_supports_deepcopy(mock_client):
    """Test that a frozen transaction can be deep-copied with its own execution lock."""
    transaction = TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))
    transaction.freeze_with(mock_client)

    clone = copy.deepcopy(transaction)

    assert clone.transaction_id == transaction.transaction_id
    assert clone._execution_lock is not transaction._execution_lock


def test_expired_later_chunk_regenerates_only_that_chunk_for_file_append():
    """Test that an expired later FileAppend chunk gets a new ID while other chunks keep theirs."""
    ok = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)
    receipt = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        )
    )
    # chunk 0 succeeds, chunk 1 expires then succeeds, chunk 2 succeeds
    sequence = [ok, receipt, _expired(), ok, receipt, ok, receipt]

    with mock_hedera_servers([sequence]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        tx = FileAppendTransaction().set_file_id(FileId(0, 0, 1234)).set_contents("ABC").set_chunk_size(1)
        tx.freeze_with(client)

        original_chunk_0_id = tx._transaction_ids.get(0)
        original_chunk_0_bodies = dict(tx._transaction_body_bytes[original_chunk_0_id])
        original_chunk_1_id = tx._transaction_ids.get(1)
        original_chunk_2_id = tx._transaction_ids.get(2)

        receipts = tx.execute_all(client)

        assert all(r.status == ResponseCode.SUCCESS for r in receipts)
        assert tx._transaction_ids.get(0) == original_chunk_0_id
        assert tx._transaction_body_bytes[original_chunk_0_id] == original_chunk_0_bodies
        assert tx._transaction_ids.get(2) == original_chunk_2_id

        new_chunk_1_id = tx._transaction_ids.get(1)
        assert new_chunk_1_id != original_chunk_1_id
        assert original_chunk_1_id not in tx._transaction_body_bytes

        for node_bytes in tx._transaction_body_bytes[new_chunk_1_id].values():
            body = transaction_pb2.TransactionBody()
            body.ParseFromString(node_bytes)
            assert body.fileAppend.contents == b"B"
            assert body.transactionID == new_chunk_1_id._to_proto()


def test_serialized_transaction_id_is_not_regenerated():
    """Test that a transaction ID already serialized with to_bytes() is not replaced on expiry."""
    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        tx = TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))
        tx.freeze_with(client)
        original_id = tx.transaction_id

        tx.to_bytes()

        with pytest.raises(PrecheckError):
            tx.execute(client)

        assert tx.transaction_id == original_id


def test_transaction_restored_from_bytes_is_not_regenerated():
    """Test that a transaction restored with from_bytes() keeps its transaction ID on expiry."""
    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        source = TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))
        source.freeze_with(client)
        original_id = source.transaction_id

        restored = Transaction.from_bytes(source.to_bytes())

        with pytest.raises(PrecheckError):
            restored.execute(client)

        assert restored.transaction_id == original_id


def test_reading_transaction_id_does_not_disable_regeneration():
    """Test that reading transaction_id after freeze does not stop an expired transaction from retrying."""
    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        tx = TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))
        tx.freeze_with(client)
        original_id = tx.transaction_id  # reading must not pin the ID

        with pytest.raises(Exception):  # noqa: B017 - mock has no reply after the retry
            tx.execute(client)

        assert tx.transaction_id != original_id


def test_batch_transaction_signed_by_batch_key_is_not_regenerated(mock_client):
    """Test that a batch signed by a non-operator batch key is not regenerated on expiry."""
    batch_key = PrivateKey.generate()

    with mock_hedera_servers([[_expired()]]) as client, patch("hiero_sdk_python.executable.time.sleep"):
        inner = (
            TransferTransaction()
            .add_hbar_transfer(AccountId(0, 0, 1001), Hbar(-1))
            .add_hbar_transfer(AccountId(0, 0, 1002), Hbar(1))
            .batchify(mock_client, batch_key)
        )
        batch = BatchTransaction().add_inner_transaction(inner).freeze_with(client).sign(batch_key)
        original_id = batch.transaction_id
        original_inner_id = inner.transaction_id

        with pytest.raises(PrecheckError):
            batch.execute(client)

        assert batch.transaction_id == original_id
        assert inner.transaction_id == original_inner_id
