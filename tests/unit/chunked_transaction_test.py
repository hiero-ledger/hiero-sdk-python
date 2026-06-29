from __future__ import annotations

from unittest.mock import patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.transaction.chunked_transaction import ChunkedTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit


class DummyChunkedTransaction(ChunkedTransaction):
    def __init__(self, required_chunks: int = 1) -> None:
        super().__init__()
        self.required_chunks = required_chunks

    def _get_method(self, _channel):
        method = type("Method", (), {})()
        method.query = None
        method.transaction = None
        return method

    def get_required_chunks(self) -> int:
        return self.required_chunks

    def _build_proto_body(self):
        return self.build_base_transaction_body()

    def build_transaction_body(self):
        return self.build_base_transaction_body()

    def build_scheduled_body(self):
        return self.build_base_scheduled_body()


def test_constructor_sets_default_chunk_configuration():
    tx = DummyChunkedTransaction()

    assert tx.chunk_size == 1024
    assert tx.max_chunks == 20
    assert tx._current_chunk_index == 0
    assert tx._total_chunks == 1
    assert tx._transaction_ids == []
    assert tx._signing_keys == []


@pytest.mark.parametrize(
    "setter_name, value, message",
    [("set_chunk_size", 0, "chunk_size must be positive"), ("set_max_chunks", 0, "max_chunks must be positive")],
)
def test_setters_reject_non_positive_values(mock_client, setter_name, value, message):
    tx = DummyChunkedTransaction()

    with pytest.raises(ValueError, match=message):
        getattr(tx, setter_name)(value)


def test_validate_chunking_rejects_zero_required_chunks():
    tx = DummyChunkedTransaction(required_chunks=0)

    with pytest.raises(ValueError, match="Transaction must require at least one chunk"):
        tx._validate_chunking()


def test_validate_chunking_rejects_too_many_chunks():
    tx = DummyChunkedTransaction(required_chunks=4).set_max_chunks(2)

    with pytest.raises(
        ValueError,
        match=r"Message requires 4 chunks but max_chunks=2\. Increase limit with set_max_chunks\(\)\.",
    ):
        tx._validate_chunking()


def test_freeze_with_builds_chunk_transaction_ids(mock_client):
    tx = DummyChunkedTransaction(required_chunks=3)
    base_timestamp = timestamp_pb2.Timestamp(seconds=123, nanos=456)
    tx.transaction_id = TransactionId(account_id=AccountId(0, 0, 1234), valid_start=base_timestamp)

    tx.freeze_with(mock_client)

    assert tx._total_chunks == 3
    assert len(tx._transaction_ids) == 3
    assert tx._initial_transaction_id == tx.transaction_id
    assert tx._transaction_ids[0] == tx.transaction_id
    assert tx._transaction_ids[1].valid_start.seconds == 123
    assert tx._transaction_ids[1].valid_start.nanos == 457
    assert tx._transaction_ids[2].valid_start.seconds == 123
    assert tx._transaction_ids[2].valid_start.nanos == 458


def test_sign_tracks_signing_keys_once(mock_client, private_key):
    tx = DummyChunkedTransaction(required_chunks=1)
    tx.freeze_with(mock_client)

    tx.sign(private_key)
    tx.sign(private_key)

    assert tx._signing_keys == [private_key]
    assert tx.is_signed_by(private_key.public_key()) is True


def test_body_size_all_chunks_restores_state(mock_client):
    tx = DummyChunkedTransaction(required_chunks=3)
    tx.transaction_id = TransactionId(
        account_id=AccountId(0, 0, 1234),
        valid_start=timestamp_pb2.Timestamp(seconds=123, nanos=456),
    )
    tx.freeze_with(mock_client)

    original_chunk_index = tx._current_chunk_index
    original_transaction_id = tx.transaction_id

    sizes = tx.body_size_all_chunks

    assert len(sizes) == 3
    assert all(size > 0 for size in sizes)
    assert tx._current_chunk_index == original_chunk_index
    assert tx.transaction_id == original_transaction_id


def test_execute_all_single_chunk_delegates_to_transaction_execute(mock_client):
    tx = DummyChunkedTransaction(required_chunks=1)
    tx.freeze_with(mock_client)

    with patch.object(Transaction, "execute", return_value="single-chunk-response") as mock_execute:
        responses = tx.execute_all(mock_client)

    assert responses == ["single-chunk-response"]
    assert mock_execute.call_count == 1
    assert mock_execute.call_args.args[0] is mock_client


def test_execute_all_multi_chunk_replays_each_chunk(mock_client, private_key):
    tx = DummyChunkedTransaction(required_chunks=3)
    tx.transaction_id = TransactionId(
        account_id=AccountId(0, 0, 1234),
        valid_start=timestamp_pb2.Timestamp(seconds=123, nanos=456),
    )
    tx.freeze_with(mock_client)
    tx.sign(private_key)

    with patch.object(Transaction, "execute", side_effect=["chunk-1", "chunk-2", "chunk-3"]) as mock_execute:
        responses = tx.execute_all(mock_client)

    assert responses == ["chunk-1", "chunk-2", "chunk-3"]
    assert mock_execute.call_count == 3
    assert tx._current_chunk_index == 2
