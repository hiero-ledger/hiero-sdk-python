"""Tests for regenerating the transaction ID on TRANSACTION_EXPIRED."""

from __future__ import annotations

import copy
from unittest.mock import patch

import pytest
from google.protobuf import timestamp_pb2

from hiero_sdk_python import executable
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.executable import _ExecutionState
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_contents_pb2,
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


def _ok():
    return transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)


def _receipt():
    return response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        )
    )


def _transfer():
    return TransferTransaction().add_hbar_transfer(AccountId(0, 0, 1001), Hbar(1))


def _body(body_bytes: bytes) -> transaction_pb2.TransactionBody:
    body = transaction_pb2.TransactionBody()
    body.ParseFromString(body_bytes)
    return body


def _submitted_transaction_ids(spy) -> list[TransactionId]:
    """Transaction IDs of every request sent to the network, in order."""
    transaction_ids = []
    for call in spy.call_args_list:
        signed_transaction = transaction_contents_pb2.SignedTransaction()
        signed_transaction.ParseFromString(call.args[1].signedTransactionBytes)
        transaction_ids.append(TransactionId._from_proto(_body(signed_transaction.bodyBytes).transactionID))
    return transaction_ids


@pytest.fixture
def no_sleep():
    with patch("hiero_sdk_python.executable.time.sleep"):
        yield


@pytest.fixture
def request_spy():
    with patch.object(executable, "_execute_method", wraps=executable._execute_method) as spy:
        yield spy


def _assert_not_regenerated(tx, client, original_id, request_spy):
    with pytest.raises(PrecheckError) as exc_info:
        tx.execute(client, wait_for_receipt=False)

    assert exc_info.value.status == ResponseCode.TRANSACTION_EXPIRED
    assert tx._current_transaction_id == original_id
    assert _submitted_transaction_ids(request_spy) == [original_id]


# Successful regeneration


def test_expiry_regenerates_id_with_operator_as_payer(no_sleep, request_spy):
    """Test that one expiry replaces the ID, rebuilds and re-signs the bodies, and retries."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = _transfer().freeze_with(client)
        old_id = tx._current_transaction_id
        old_body_bytes = list(tx._transaction_body_bytes[old_id].values())

        response = tx.execute(client, wait_for_receipt=False)

        new_id = tx._current_transaction_id
        assert new_id != old_id
        assert new_id.account_id == client.operator_account_id
        assert response.transaction_id == new_id
        assert _submitted_transaction_ids(request_spy) == [old_id, new_id]

        # The old bodies and their signatures are gone.
        assert list(tx._transaction_body_bytes) == [new_id]
        assert all(body_bytes not in tx._signature_map for body_bytes in old_body_bytes)

        operator_public_key = client.operator_private_key.public_key()
        new_bodies = tx._transaction_body_bytes[new_id]
        assert set(tx._signature_map) == set(new_bodies.values())
        for node_account_id, body_bytes in new_bodies.items():
            body = _body(body_bytes)
            assert body.transactionID == new_id._to_proto()
            assert body.nodeAccountID == node_account_id._to_proto()

            sig_pairs = tx._signature_map[body_bytes].sigPair
            assert len(sig_pairs) == 1
            assert sig_pairs[0].pubKeyPrefix == operator_public_key.to_bytes_raw()
            operator_public_key.verify(sig_pairs[0].ed25519, body_bytes)

        # The ID list stays locked after regeneration.
        with pytest.raises(RuntimeError):
            tx._transaction_ids.set(0, old_id)


def test_transaction_id_read_after_execute_matches_response(no_sleep):
    """Test that the public transaction_id after execute() is the regenerated one."""
    with mock_hedera_servers([[_expired(), _ok(), _receipt()]]) as client:
        tx = _transfer().freeze_with(client)
        old_id = tx._current_transaction_id

        response = tx.execute(client, wait_for_receipt=False)
        receipt = response.get_receipt(client)

        assert receipt.status == ResponseCode.SUCCESS
        assert tx.transaction_id == response.transaction_id
        assert tx.transaction_id != old_id


def test_second_expiry_raises_precheck_error_after_one_regeneration(no_sleep, request_spy):
    """Test that a second expiry in the same execute() raises instead of regenerating again."""
    with mock_hedera_servers([[_expired(), _expired(), _expired(), _expired()]]) as client:
        tx = _transfer().freeze_with(client)
        old_id = tx._current_transaction_id

        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client, wait_for_receipt=False)

        new_id = tx._current_transaction_id
        assert exc_info.value.status == ResponseCode.TRANSACTION_EXPIRED
        assert exc_info.value.transaction_id == new_id
        assert _submitted_transaction_ids(request_spy) == [old_id, new_id]


def test_reading_transaction_id_before_freeze_does_not_pin(no_sleep, request_spy):
    """Test that reading an unset transaction_id (None) does not pin the later generated ID."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = _transfer()
        assert tx.transaction_id is None

        tx.freeze_with(client)
        old_id = tx._current_transaction_id
        tx.execute(client, wait_for_receipt=False)

        assert tx._current_transaction_id != old_id


def test_explicit_operator_signature_does_not_block_regeneration(no_sleep):
    """Test that signing with the operator key yourself still allows regeneration."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = _transfer().freeze_with(client).sign(client.operator_private_key)
        old_id = tx._current_transaction_id

        tx.execute(client, wait_for_receipt=False)

        assert tx._current_transaction_id != old_id


def test_freeze_with_twice_on_topic_create_does_not_pin(no_sleep):
    """Test that TopicCreateTransaction.freeze_with() reads the ID without pinning it."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = TopicCreateTransaction().set_memo("memo")
        tx.freeze_with(client)
        tx.freeze_with(client)
        old_id = tx._current_transaction_id

        tx.execute(client, wait_for_receipt=False)

        assert tx._current_transaction_id != old_id


# Enabling and disabling


@pytest.mark.parametrize(
    ("client_default", "transaction_setting", "expect_regenerated"),
    [
        (True, None, True),
        (False, None, False),
        (True, False, False),
        (False, True, True),
    ],
)
def test_transaction_setting_overrides_client_default(
    no_sleep, client_default, transaction_setting, expect_regenerated
):
    """Test that the transaction setting wins and the client default applies otherwise."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        client.set_default_regenerate_transaction_id(client_default)
        tx = _transfer()
        if transaction_setting is not None:
            tx.set_regenerate_transaction_id(transaction_setting)
        tx.freeze_with(client)
        old_id = tx._current_transaction_id

        if expect_regenerated:
            tx.execute(client, wait_for_receipt=False)
            assert tx._current_transaction_id != old_id
        else:
            with pytest.raises(PrecheckError):
                tx.execute(client, wait_for_receipt=False)
            assert tx._current_transaction_id == old_id


def test_refreezing_does_not_change_resolved_setting(mock_client):
    """Test that a second freeze_with() does not re-resolve regenerate_transaction_id."""
    tx = _transfer().freeze_with(mock_client)
    assert tx.regenerate_transaction_id is True

    mock_client.set_default_regenerate_transaction_id(False)
    tx.freeze_with(mock_client)

    assert tx.regenerate_transaction_id is True


# Pinning


def _pin_by_set(tx, client):
    return tx.set_transaction_id(TransactionId.generate(client.operator_account_id)).freeze_with(client)


def _pin_by_setter(tx, client):
    tx.transaction_id = TransactionId.generate(client.operator_account_id)
    return tx.freeze_with(client)


def _pin_by_read(tx, client):
    tx.freeze_with(client)
    _ = tx.transaction_id
    return tx


def _pin_by_to_bytes(tx, client):
    tx.freeze_with(client)
    tx.to_bytes()
    return tx


def _pin_by_from_bytes(tx, client):
    return Transaction.from_bytes(tx.freeze_with(client).to_bytes())


@pytest.mark.parametrize(
    "pin",
    [_pin_by_set, _pin_by_setter, _pin_by_read, _pin_by_to_bytes, _pin_by_from_bytes],
    ids=["set_transaction_id", "transaction_id_setter", "read", "to_bytes", "from_bytes"],
)
def test_pinned_transaction_id_is_not_regenerated(no_sleep, request_spy, pin):
    """Test that each pin trigger keeps the ID and raises PrecheckError on expiry."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = pin(_transfer(), client)
        _assert_not_regenerated(tx, client, tx._current_transaction_id, request_spy)


def test_user_set_transaction_id_is_not_regenerated_for_chunked_transaction(no_sleep, topic_id):
    """Test that a caller-supplied ID on a chunked transaction is not replaced on expiry."""
    with mock_hedera_servers([[_expired()]]) as client:
        user_transaction_id = TransactionId.generate(client.operator_account_id)
        tx = (
            TopicMessageSubmitTransaction()
            .set_topic_id(topic_id)
            .set_message("ABCD")
            .set_chunk_size(1)
            .set_transaction_id(user_transaction_id)
            .freeze_with(client)
        )
        original_ids = list(tx._transaction_ids)

        with pytest.raises(PrecheckError):
            tx.execute_all(client, wait_for_receipt=False)

        assert list(tx._transaction_ids) == original_ids
        assert tx._initial_transaction_id == user_transaction_id


# Payer, signer and type guards


def test_payer_other_than_executing_operator_is_not_regenerated(no_sleep, request_spy, mock_client):
    """Test that an ID paid for by an account other than the executing operator is kept."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        tx = _transfer().freeze_with(mock_client)
        assert tx._current_transaction_id.account_id != client.operator_account_id

        _assert_not_regenerated(tx, client, tx._current_transaction_id, request_spy)


def test_non_operator_signature_blocks_regeneration(no_sleep, request_spy):
    """Test that a signature the SDK cannot reproduce keeps the ID."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        other_key = PrivateKey.generate()
        tx = _transfer().freeze_with(client).sign(other_key)

        _assert_not_regenerated(tx, client, tx._current_transaction_id, request_spy)
        assert tx.is_signed_by(other_key.public_key())


@pytest.mark.parametrize("batch_key_is_operator", [True, False])
def test_batch_transaction_is_never_regenerated(no_sleep, request_spy, batch_key_is_operator):
    """Test that a BatchTransaction keeps its ID, even when only the operator signed it."""
    with mock_hedera_servers([[_expired(), _ok()]]) as client:
        batch_key = client.operator_private_key if batch_key_is_operator else PrivateKey.generate()
        inner = (
            TransferTransaction()
            .add_hbar_transfer(AccountId(0, 0, 1001), Hbar(-1))
            .add_hbar_transfer(AccountId(0, 0, 1002), Hbar(1))
            .batchify(client, batch_key)
        )
        inner_id = inner._current_transaction_id
        batch = BatchTransaction().add_inner_transaction(inner).freeze_with(client).sign(batch_key)

        _assert_not_regenerated(batch, client, batch._current_transaction_id, request_spy)
        assert inner._current_transaction_id == inner_id


# Execution-scoped operator state


def test_should_retry_returns_expired_outside_execute(mock_client):
    """Test that TRANSACTION_EXPIRED is not retried when no execute() regeneration context is active."""
    tx = _transfer().freeze_with(mock_client).sign(mock_client.operator_private_key)

    assert tx._should_retry(_expired()) == _ExecutionState.EXPIRED


@pytest.mark.parametrize("responses", [[_expired(), _ok()], [_expired(), _expired()]], ids=["success", "failure"])
def test_no_operator_state_remains_after_execute(no_sleep, responses):
    """Test that the operator key is only held while execute() runs."""
    with mock_hedera_servers([responses]) as client:
        tx = _transfer().freeze_with(client)

        contexts = []
        original_can_regenerate = Transaction._can_regenerate_transaction_id

        def record_context(self):
            contexts.append(self._regeneration_context)
            return original_can_regenerate(self)

        with patch.object(Transaction, "_can_regenerate_transaction_id", record_context):
            try:
                tx.execute(client, wait_for_receipt=False)
            except PrecheckError:
                pass

        assert contexts[0].operator_private_key is client.operator_private_key
        assert tx._regeneration_context is None
        assert not hasattr(tx, "operator_private_key")
        assert not any(isinstance(value, PrivateKey) for value in vars(tx).values())

        assert copy.deepcopy(tx)._current_transaction_id == tx._current_transaction_id


# Chunked transactions


def _chunk_bodies(tx):
    """(transaction ID, parsed body) for every node body of every chunk, in chunk order."""
    return [
        (transaction_id, _body(body_bytes))
        for transaction_id in tx._transaction_ids
        for body_bytes in tx._transaction_body_bytes[transaction_id].values()
    ]


def _assert_consecutive(transaction_ids):
    assert transaction_ids == Transaction._consecutive_transaction_ids(transaction_ids[0], len(transaction_ids))


def test_topic_message_later_chunk_expiry_regenerates_current_and_later_chunks(no_sleep, topic_id, request_spy):
    """Test that chunk 2 expiring regenerates chunks 2..n and leaves chunk 1 untouched."""
    with mock_hedera_servers([[_ok(), _expired(), _ok(), _ok(), _ok()]]) as client:
        tx = TopicMessageSubmitTransaction().set_topic_id(topic_id).set_message("ABCD").set_chunk_size(1)
        tx.freeze_with(client)

        old_ids = list(tx._transaction_ids)
        initial_id = tx._initial_transaction_id
        chunk_1_bodies = dict(tx._transaction_body_bytes[old_ids[0]])

        tx.execute_all(client, wait_for_receipt=False)

        new_ids = list(tx._transaction_ids)
        assert new_ids[0] == old_ids[0]
        assert tx._transaction_body_bytes[old_ids[0]] == chunk_1_bodies
        assert all(body in tx._signature_map for body in chunk_1_bodies.values())
        assert all(new != old for new, old in zip(new_ids[1:], old_ids[1:], strict=True))
        assert all(old not in tx._transaction_body_bytes for old in old_ids[1:])
        _assert_consecutive(new_ids[1:])

        assert tx._initial_transaction_id == initial_id
        assert _submitted_transaction_ids(request_spy) == [old_ids[0], old_ids[1], *new_ids[1:]]

        for transaction_id, body in _chunk_bodies(tx):
            index = new_ids.index(transaction_id)
            chunk = body.consensusSubmitMessage
            assert body.transactionID == transaction_id._to_proto()
            assert transaction_id.account_id == initial_id.account_id
            assert chunk.chunkInfo.initialTransactionID == initial_id._to_proto()
            assert chunk.chunkInfo.number == index + 1
            assert chunk.chunkInfo.total == 4
            assert chunk.message == b"ABCD"[index : index + 1]


def test_topic_message_first_chunk_expiry_moves_initial_transaction_id(no_sleep, topic_id):
    """Test that the first chunk expiring regenerates every chunk and moves the initial ID."""
    with mock_hedera_servers([[_expired(), _ok(), _ok(), _ok(), _ok()]]) as client:
        tx = TopicMessageSubmitTransaction().set_topic_id(topic_id).set_message("ABCD").set_chunk_size(1)
        tx.freeze_with(client)
        old_ids = list(tx._transaction_ids)

        tx.execute_all(client, wait_for_receipt=False)

        new_ids = list(tx._transaction_ids)
        assert all(new != old for new, old in zip(new_ids, old_ids, strict=True))
        _assert_consecutive(new_ids)
        assert tx._initial_transaction_id == new_ids[0]

        for transaction_id, body in _chunk_bodies(tx):
            index = new_ids.index(transaction_id)
            chunk = body.consensusSubmitMessage
            assert chunk.chunkInfo.initialTransactionID == new_ids[0]._to_proto()
            assert chunk.chunkInfo.number == index + 1
            assert chunk.message == b"ABCD"[index : index + 1]


def test_file_append_later_chunk_expiry_preserves_chunk_contents(no_sleep):
    """Test that a regenerated FileAppend chunk keeps its own contents."""
    with mock_hedera_servers([[_ok(), _expired(), _ok(), _ok()]]) as client:
        tx = FileAppendTransaction().set_file_id(FileId(0, 0, 1234)).set_contents("ABC").set_chunk_size(1)
        tx.freeze_with(client)
        old_ids = list(tx._transaction_ids)
        chunk_1_bodies = dict(tx._transaction_body_bytes[old_ids[0]])

        tx.execute_all(client, wait_for_receipt=False)

        new_ids = list(tx._transaction_ids)
        assert new_ids[0] == old_ids[0]
        assert tx._transaction_body_bytes[old_ids[0]] == chunk_1_bodies
        assert all(new != old for new, old in zip(new_ids[1:], old_ids[1:], strict=True))

        for transaction_id, body in _chunk_bodies(tx):
            assert body.fileAppend.contents == b"ABC"[new_ids.index(transaction_id)].to_bytes(1, "big")


# Consecutive transaction IDs


def test_consecutive_transaction_ids_roll_over_second_boundary():
    """Test that consecutive IDs carry nanoseconds over into the next second."""
    payer = AccountId(0, 0, 1800)
    initial_id = TransactionId(payer, timestamp_pb2.Timestamp(seconds=100, nanos=999_999_998))

    transaction_ids = Transaction._consecutive_transaction_ids(initial_id, 4)

    assert transaction_ids[0] is initial_id
    assert [(t.valid_start.seconds, t.valid_start.nanos) for t in transaction_ids] == [
        (100, 999_999_998),
        (100, 999_999_999),
        (101, 0),
        (101, 1),
    ]
    assert all(t.account_id == payer for t in transaction_ids)


@pytest.mark.parametrize("count", [0, 1])
def test_consecutive_transaction_ids_small_counts(count):
    """Test the single-ID and empty cases."""
    initial_id = TransactionId(AccountId(0, 0, 1800), timestamp_pb2.Timestamp(seconds=100, nanos=5))

    assert Transaction._consecutive_transaction_ids(initial_id, count) == [initial_id][:count]


def test_max_attempts_is_not_reached_by_repeated_expiry(no_sleep):
    """Test that repeated expiry surfaces as PrecheckError rather than MaxAttemptsError."""
    with mock_hedera_servers([[_expired()] * 4]) as client:
        tx = _transfer().freeze_with(client)

        with pytest.raises(PrecheckError) as exc_info:
            tx.execute(client, wait_for_receipt=False)

        assert not isinstance(exc_info.value, MaxAttemptsError)
