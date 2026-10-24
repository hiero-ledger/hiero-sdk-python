"""
Unit tests for restoring chunked transactions from a serialized TransactionList.

Transaction.from_bytes() must reject chunk groups of a FileAppendTransaction or
TopicMessageSubmitTransaction that are out of order, incomplete, or belong to
different chunked transactions, while valid lists still round-trip unchanged.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.sdk.transaction_list_pb2 import TransactionList
from hiero_sdk_python.hapi.services import transaction_contents_pb2, transaction_pb2
from hiero_sdk_python.transaction.chunked_transaction import ChunkedTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit

BodyRewrite = Callable[[int, transaction_pb2.TransactionBody], None]


def _file_append_transaction(node_account_ids: list[AccountId], contents: bytes = b"AAAABBBB") -> FileAppendTransaction:
    """Return a frozen FileAppendTransaction with one chunk per 4 bytes of contents."""
    return (
        FileAppendTransaction()
        .set_file_id(FileId(0, 0, 101))
        .set_chunk_size(4)
        .set_contents(contents)
        .set_transaction_id(TransactionId.from_string("0.0.1001@1700000000.0"))
        .set_node_account_ids(node_account_ids)
        .freeze()
    )


def _topic_message_transaction(
    node_account_ids: list[AccountId], message: bytes = b"AAAABBBB"
) -> TopicMessageSubmitTransaction:
    """Return a frozen TopicMessageSubmitTransaction with one chunk per 4 bytes of message."""
    return (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId(0, 0, 1234))
        .set_chunk_size(4)
        .set_message(message)
        .set_transaction_id(TransactionId.from_string("0.0.1001@1700000000.0"))
        .set_node_account_ids(node_account_ids)
        .freeze()
    )


@pytest.fixture(params=[_file_append_transaction, _topic_message_transaction], ids=["file_append", "topic_message"])
def build_chunked_transaction(request) -> Callable[..., ChunkedTransaction]:
    """Fixture that provides a builder for each chunked transaction type."""
    return request.param


@pytest.fixture(
    params=[[AccountId(0, 0, 3)], [AccountId(0, 0, 3), AccountId(0, 0, 4)]],
    ids=["single_node", "multiple_nodes"],
)
def node_account_ids(request) -> list[AccountId]:
    """Fixture that provides the node account IDs each chunk is built for."""
    return request.param


def _rewrite_bodies(tx_bytes: bytes, node_count: int, rewrite: BodyRewrite) -> bytes:
    """Apply rewrite(chunk_index, body) to every body in a TransactionList and re-serialize it."""
    transaction_list = TransactionList.FromString(tx_bytes)

    for index, transaction in enumerate(transaction_list.transaction_list):
        signed_transaction = transaction_contents_pb2.SignedTransaction.FromString(transaction.signedTransactionBytes)
        body = transaction_pb2.TransactionBody.FromString(signed_transaction.bodyBytes)

        rewrite(index // node_count, body)

        signed_transaction.bodyBytes = body.SerializeToString()
        transaction.signedTransactionBytes = signed_transaction.SerializeToString()

    return transaction_list.SerializeToString()


def _set_valid_start_nanos(tx_bytes: bytes, node_count: int, nanos: list[int]) -> bytes:
    """Re-time each chunk's transaction ID, keeping a topic message's initial transaction ID on chunk 1."""

    def rewrite(chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
        body.transactionID.transactionValidStart.nanos = nanos[chunk_index]

        if body.consensusSubmitMessage.HasField("chunkInfo"):
            body.consensusSubmitMessage.chunkInfo.initialTransactionID.transactionValidStart.nanos = nanos[0]

    return _rewrite_bodies(tx_bytes, node_count, rewrite)


def _swap_first_chunk_groups(tx_bytes: bytes, node_count: int) -> bytes:
    """Return the TransactionList with its first two chunk groups swapped."""
    transactions = list(TransactionList.FromString(tx_bytes).transaction_list)
    first_group = transactions[:node_count]
    second_group = transactions[node_count : 2 * node_count]

    return TransactionList(
        transaction_list=second_group + first_group + transactions[2 * node_count :]
    ).SerializeToString()


@pytest.mark.parametrize("contents", [b"AAAA", b"AAAABBBB", b"AAAABBBBCC"], ids=["1_chunk", "2_chunks", "3_chunks"])
@pytest.mark.parametrize("signed", [False, True], ids=["unsigned", "signed"])
def test_from_bytes_round_trips_chunked_transaction(build_chunked_transaction, node_account_ids, contents, signed):
    """Test that frozen chunked transactions restore and re-serialize to identical bytes."""
    tx = build_chunked_transaction(node_account_ids, contents)

    if signed:
        tx.sign(PrivateKey.generate_ed25519())

    tx_bytes = tx.to_bytes()
    restored = Transaction.from_bytes(tx_bytes)

    assert type(restored) is type(tx)
    assert restored._transaction_ids.get_list() == tx._transaction_ids.get_list()
    assert restored.to_bytes() == tx_bytes


def test_from_bytes_accepts_wider_chunk_interval(build_chunked_transaction, node_account_ids):
    """Test that chunk valid starts only need to increase, since other SDKs space chunks by more than 1ns."""
    tx = build_chunked_transaction(node_account_ids, b"AAAABBBBCC")
    tx_bytes = _set_valid_start_nanos(tx.to_bytes(), len(node_account_ids), [0, 10, 20])

    restored = Transaction.from_bytes(tx_bytes)

    assert [transaction_id.valid_start.nanos for transaction_id in restored._transaction_ids] == [0, 10, 20]
    assert restored.to_bytes() == tx_bytes


def test_from_bytes_accepts_single_chunk_topic_message_with_chunk_info(node_account_ids):
    """Test that a single-chunk topic message carrying chunk info (as the JS SDK serializes it) is accepted."""
    tx = _topic_message_transaction(node_account_ids, b"AAAA")

    def add_chunk_info(_chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
        chunk_info = body.consensusSubmitMessage.chunkInfo
        chunk_info.initialTransactionID.CopyFrom(body.transactionID)
        chunk_info.total = 1
        chunk_info.number = 1

    tx_bytes = _rewrite_bodies(tx.to_bytes(), len(node_account_ids), add_chunk_info)

    assert Transaction.from_bytes(tx_bytes).to_bytes() == tx_bytes


def test_from_bytes_rejects_swapped_chunk_groups(build_chunked_transaction, node_account_ids):
    """Test that a TransactionList whose chunk groups were reordered is rejected."""
    tx = build_chunked_transaction(node_account_ids)
    swapped_bytes = _swap_first_chunk_groups(tx.to_bytes(), len(node_account_ids))

    with pytest.raises(ValueError, match="chunks are out of order, chunk 2 does not start after chunk 1"):
        Transaction.from_bytes(swapped_bytes)


def test_from_bytes_rejects_chunks_with_different_payers(build_chunked_transaction, node_account_ids):
    """Test that chunks paid for by different accounts are rejected."""
    tx = build_chunked_transaction(node_account_ids)

    def change_second_chunk_payer(chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
        if chunk_index == 1:
            body.transactionID.accountID.CopyFrom(AccountId(0, 0, 1002)._to_proto())

    tx_bytes = _rewrite_bodies(tx.to_bytes(), len(node_account_ids), change_second_chunk_payer)

    with pytest.raises(ValueError, match="chunk 2 has a different payer account than chunk 1"):
        Transaction.from_bytes(tx_bytes)


@pytest.mark.parametrize(
    "nanos, error",
    [
        ([10, 5], "chunks are out of order, chunk 2 does not start after chunk 1"),
        ([0, 2, 1], "chunks are out of order, chunk 3 does not start after chunk 2"),
        # Equal valid starts make the chunk transaction IDs identical, which the transaction-node pair check rejects
        ([0, 0], r"^Failed to validate transaction bodies$"),
    ],
    ids=["decreasing", "decreasing_later_chunk", "equal"],
)
def test_from_bytes_rejects_non_increasing_valid_start(build_chunked_transaction, node_account_ids, nanos, error):
    """Test that chunk transaction IDs must have strictly increasing valid starts."""
    contents = b"AAAA" * len(nanos)
    tx = build_chunked_transaction(node_account_ids, contents)
    tx_bytes = _set_valid_start_nanos(tx.to_bytes(), len(node_account_ids), nanos)

    with pytest.raises(ValueError, match=error):
        Transaction.from_bytes(tx_bytes)


def _swap_chunk_numbers(chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
    body.consensusSubmitMessage.chunkInfo.number = 2 - chunk_index


def _overstate_chunk_total(_chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
    body.consensusSubmitMessage.chunkInfo.total = 3


def _point_initial_transaction_id_at_own_chunk(_chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
    body.consensusSubmitMessage.chunkInfo.initialTransactionID.CopyFrom(body.transactionID)


def _point_initial_transaction_id_at_other_transaction(
    _chunk_index: int, body: transaction_pb2.TransactionBody
) -> None:
    other_transaction_id = TransactionId.from_string("0.0.1001@1600000000.0")
    body.consensusSubmitMessage.chunkInfo.initialTransactionID.CopyFrom(other_transaction_id._to_proto())


def _drop_second_chunk_info(chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
    if chunk_index == 1:
        body.consensusSubmitMessage.ClearField("chunkInfo")


@pytest.mark.parametrize(
    "rewrite, error",
    [
        (_swap_chunk_numbers, "chunk 1 has chunk number 2"),
        (_overstate_chunk_total, "chunk 1 has chunk total 3, expected 2"),
        (_point_initial_transaction_id_at_own_chunk, "chunk 2 initial transaction ID does not match"),
        (_point_initial_transaction_id_at_other_transaction, "chunk 1 initial transaction ID does not match"),
        (_drop_second_chunk_info, "chunk 2 is missing chunk info"),
    ],
    ids=["wrong_number", "wrong_total", "initial_id_per_chunk", "initial_id_elsewhere", "missing_chunk_info"],
)
def test_from_bytes_rejects_inconsistent_topic_message_chunk_info(node_account_ids, rewrite, error):
    """Test that topic message chunk info must match the chunk sequence."""
    tx = _topic_message_transaction(node_account_ids)
    tx_bytes = _rewrite_bodies(tx.to_bytes(), len(node_account_ids), rewrite)

    with pytest.raises(ValueError, match=error):
        Transaction.from_bytes(tx_bytes)


def test_from_bytes_rejects_incomplete_topic_message(node_account_ids):
    """Test that a topic message missing its last chunk group is rejected."""
    tx = _topic_message_transaction(node_account_ids)
    transactions = TransactionList.FromString(tx.to_bytes()).transaction_list
    first_group_bytes = TransactionList(transaction_list=transactions[: len(node_account_ids)]).SerializeToString()

    with pytest.raises(ValueError, match="chunk 1 has chunk total 2, expected 1"):
        Transaction.from_bytes(first_group_bytes)


def _clear_node_account_id(_chunk_index: int, body: transaction_pb2.TransactionBody) -> None:
    body.ClearField("nodeAccountID")


def test_from_bytes_accepts_ordered_chunks_without_node_account_ids(build_chunked_transaction):
    """Test that in-order chunks without node account IDs are still accepted."""
    tx = build_chunked_transaction([AccountId(0, 0, 3)])
    tx_bytes = _rewrite_bodies(tx.to_bytes(), 1, _clear_node_account_id)

    restored = Transaction.from_bytes(tx_bytes)

    assert type(restored) is type(tx)
    assert restored._transaction_ids.get_list() == tx._transaction_ids.get_list()


def test_from_bytes_rejects_swapped_chunks_without_node_account_ids(build_chunked_transaction):
    """Test that chunk order is validated even when the bodies have no node account IDs."""
    tx = build_chunked_transaction([AccountId(0, 0, 3)])
    tx_bytes = _rewrite_bodies(tx.to_bytes(), 1, _clear_node_account_id)

    with pytest.raises(ValueError, match="chunks are out of order, chunk 2 does not start after chunk 1"):
        Transaction.from_bytes(_swap_first_chunk_groups(tx_bytes, 1))
