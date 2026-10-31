"""Unit tests for signature inspection: signable_node_body_bytes_list, get_signatures and the hash getters."""

from __future__ import annotations

import hashlib
import warnings

import grpc
import pytest

from hiero_sdk_python import SignableNodeTransactionBodyBytes
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.signer import _signature_pair_to_key_and_signature
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_pb2, transaction_response_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.unit.mock_server import RealRpcError, mock_hedera_servers


pytestmark = pytest.mark.unit

NODE_IDS = [AccountId(0, 0, 3), AccountId(0, 0, 4), AccountId(0, 0, 5)]
PAYER_ID = AccountId(0, 0, 1984)


def _transfer(node_ids: list[AccountId] = NODE_IDS) -> TransferTransaction:
    return (
        TransferTransaction()
        .add_hbar_transfer(PAYER_ID, -1)
        .add_hbar_transfer(AccountId(0, 0, 2), 1)
        .set_transaction_id(TransactionId.generate(PAYER_ID))
        .set_node_account_ids(node_ids)
    )


def _file_append(file_id, chunks: int = 3, node_ids: list[AccountId] = NODE_IDS[:2]) -> FileAppendTransaction:
    return (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_chunk_size(10)
        .set_contents(b"a" * 10 * chunks)
        .set_transaction_id(TransactionId.generate(PAYER_ID))
        .set_node_account_ids(node_ids)
    )


def _assert_signatures_verify(signatures: dict, node_bodies: dict[AccountId, bytes], keys: list[PrivateKey]):
    assert set(signatures) == set(node_bodies)
    for node_account_id, key_signatures in signatures.items():
        assert set(key_signatures) == {key.public_key() for key in keys}
        for public_key, signature in key_signatures.items():
            public_key.verify(signature, node_bodies[node_account_id])


def test_signable_node_transaction_body_bytes_is_frozen():
    """Test that SignableNodeTransactionBodyBytes is immutable."""
    entry = SignableNodeTransactionBodyBytes(NODE_IDS[0], TransactionId.generate(PAYER_ID), b"body")

    with pytest.raises(AttributeError):
        entry.signable_transaction_body_bytes = b"other"


def test_signable_node_body_bytes_list_has_one_entry_per_node():
    """Test that a plain transaction gives one entry per node, in node order."""
    tx = _transfer().freeze()

    entries = tx.signable_node_body_bytes_list

    assert [entry.node_account_id for entry in entries] == NODE_IDS
    assert all(entry.transaction_id == tx.transaction_id for entry in entries)


def test_signable_node_body_bytes_list_groups_chunks_by_transaction_id(file_id):
    """Test that a chunked transaction gives chunks x nodes entries, grouped by transaction ID."""
    tx = _file_append(file_id, chunks=3).freeze()
    transaction_ids = tx._transaction_ids.get_list()

    entries = tx.signable_node_body_bytes_list

    assert len(transaction_ids) == 3
    assert [(entry.transaction_id, entry.node_account_id) for entry in entries] == [
        (transaction_id, node_account_id) for transaction_id in transaction_ids for node_account_id in NODE_IDS[:2]
    ]


def test_signable_node_body_bytes_list_matches_stored_bodies(file_id):
    """Test that each entry holds the exact stored body, whose IDs match the entry's fields."""
    tx = _file_append(file_id).freeze()

    for entry in tx.signable_node_body_bytes_list:
        stored = tx._transaction_body_bytes[entry.transaction_id][entry.node_account_id]
        assert entry.signable_transaction_body_bytes == stored

        body = transaction_pb2.TransactionBody.FromString(entry.signable_transaction_body_bytes)
        assert AccountId._from_proto(body.nodeAccountID) == entry.node_account_id
        assert TransactionId._from_proto(body.transactionID) == entry.transaction_id


@pytest.mark.parametrize("key", [PrivateKey.generate_ed25519(), PrivateKey.generate_ecdsa()])
def test_signable_node_body_bytes_list_signed_externally_verifies(key):
    """Test that signing an entry's bytes externally gives the signature the transaction would hold."""
    tx = _transfer().freeze()
    entries = tx.signable_node_body_bytes_list

    tx.sign(key)

    signatures = tx.get_signatures()
    for entry in entries:
        external_signature = key.sign(entry.signable_transaction_body_bytes)
        key.public_key().verify(external_signature, entry.signable_transaction_body_bytes)
        key.public_key().verify(
            signatures[entry.node_account_id][key.public_key()], entry.signable_transaction_body_bytes
        )


def test_signable_node_body_bytes_list_requires_frozen_transaction():
    """Test that signable_node_body_bytes_list raises on an unfrozen transaction."""
    with pytest.raises(Exception, match="Transaction is not frozen"):
        _ = _transfer().signable_node_body_bytes_list


def test_get_signatures_returns_every_key_for_every_node():
    """Test that each node maps both an Ed25519 and an ECDSA key to a signature over its body."""
    keys = [PrivateKey.generate_ed25519(), PrivateKey.generate_ecdsa()]
    tx = _transfer().freeze()
    for key in keys:
        tx.sign(key)

    signatures = tx.get_signatures()

    _assert_signatures_verify(signatures, tx._transaction_body_bytes[tx.transaction_id], keys)


def test_get_signatures_defaults_to_first_transaction_id(file_id):
    """Test that a chunked transaction returns the first chunk's signatures by default."""
    key = PrivateKey.generate_ed25519()
    tx = _file_append(file_id).freeze().sign(key)
    first_transaction_id = tx._transaction_ids.get(0)

    assert tx.get_signatures() == tx.get_signatures(first_transaction_id)
    _assert_signatures_verify(tx.get_signatures(), tx._transaction_body_bytes[first_transaction_id], [key])


def test_get_signatures_for_chunk_returns_that_chunk_only(file_id):
    """Test that passing a chunk's transaction ID returns the signatures over that chunk's bodies."""
    key = PrivateKey.generate_ecdsa()
    tx = _file_append(file_id).freeze().sign(key)
    first_transaction_id, second_transaction_id = tx._transaction_ids.get_list()[:2]

    signatures = tx.get_signatures(second_transaction_id)

    _assert_signatures_verify(signatures, tx._transaction_body_bytes[second_transaction_id], [key])
    assert signatures != tx.get_signatures(first_transaction_id)


def test_get_signatures_unknown_transaction_id_raises():
    """Test that a transaction ID the transaction does not hold raises ValueError."""
    tx = _transfer().freeze()

    with pytest.raises(ValueError, match="No transaction bodies built for Transaction ID"):
        tx.get_signatures(TransactionId.generate(AccountId(0, 0, 9999)))


def test_get_signatures_rejects_non_transaction_id():
    """Test that a transaction_id of the wrong type raises TypeError."""
    tx = _transfer().freeze()

    with pytest.raises(TypeError, match="transaction_id must be of type TransactionId"):
        tx.get_signatures(str(tx.transaction_id))


def test_get_signatures_unsigned_transaction_maps_every_node_to_empty_dict():
    """Test that an unsigned frozen transaction lists every node with no signatures."""
    tx = _transfer().freeze()

    assert tx.get_signatures() == {node_account_id: {} for node_account_id in NODE_IDS}


def test_get_signatures_result_is_a_copy():
    """Test that mutating the result does not change the transaction."""
    key = PrivateKey.generate_ed25519()
    tx = _transfer().freeze().sign(key)

    signatures = tx.get_signatures()
    signatures[NODE_IDS[0]].clear()
    signatures.pop(NODE_IDS[1])

    _assert_signatures_verify(tx.get_signatures(), tx._transaction_body_bytes[tx.transaction_id], [key])


def test_get_signatures_on_restored_transaction():
    """Test that signatures survive a to_bytes / from_bytes round trip."""
    keys = [PrivateKey.generate_ed25519(), PrivateKey.generate_ecdsa()]
    tx = _transfer().freeze()
    for key in keys:
        tx.sign(key)

    restored = Transaction.from_bytes(tx.to_bytes())

    assert restored.get_signatures() == tx.get_signatures()
    _assert_signatures_verify(
        restored.get_signatures(), restored._transaction_body_bytes[restored.transaction_id], keys
    )


def test_get_signatures_requires_frozen_transaction():
    """Test that get_signatures raises on an unfrozen transaction."""
    with pytest.raises(Exception, match="Transaction is not frozen"):
        _transfer().get_signatures()


def test_get_signatures_rejects_shortened_public_key_prefix():
    """Test that a signature with a shortened pubKeyPrefix raises a clear ValueError."""
    key = PrivateKey.generate_ed25519()
    tx = _transfer().freeze()
    body = tx._transaction_body_bytes[tx.transaction_id][NODE_IDS[0]]
    tx._signature_map[body] = basic_types_pb2.SignatureMap(
        sigPair=[
            basic_types_pb2.SignaturePair(pubKeyPrefix=key.public_key().to_bytes_raw()[:6], ed25519=key.sign(body))
        ]
    )

    with pytest.raises(ValueError, match="pubKeyPrefix must be the full public key"):
        tx.get_signatures()


@pytest.mark.parametrize("key", [PrivateKey.generate_ed25519(), PrivateKey.generate_ecdsa()])
def test_signature_pair_to_key_and_signature_round_trips(key):
    """Test that unwrapping a signature pair gives back the key and signature, without warnings."""
    signature = key.sign(b"body")
    field = "ed25519" if key.is_ed25519() else "ECDSA_secp256k1"
    sig_pair = basic_types_pb2.SignaturePair(pubKeyPrefix=key.public_key().to_bytes_raw(), **{field: signature})

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        public_key, unwrapped_signature = _signature_pair_to_key_and_signature(sig_pair)

    assert public_key == key.public_key()
    assert public_key.is_ed25519() == key.is_ed25519()
    assert unwrapped_signature == signature


def test_signature_pair_to_key_and_signature_rejects_unsupported_type():
    """Test that a signature type other than Ed25519 or ECDSA (secp256k1) raises ValueError."""
    sig_pair = basic_types_pb2.SignaturePair(pubKeyPrefix=b"\x01" * 32, RSA_3072=b"signature")

    with pytest.raises(ValueError, match="Unsupported signature type: RSA_3072"):
        _signature_pair_to_key_and_signature(sig_pair)


def test_transaction_hash_is_sha384_of_the_request():
    """Test that the hash is 48 bytes and is the SHA-384 of the signed bytes that would be sent."""
    tx = _transfer().freeze().sign(PrivateKey.generate_ed25519())

    transaction_hash = tx.get_transaction_hash()

    assert len(transaction_hash) == 48
    assert transaction_hash == hashlib.sha384(tx._make_request().signedTransactionBytes).digest()


def test_transaction_hash_is_stable_until_a_signature_is_added():
    """Test that repeated calls agree and that adding a signature changes the hashes."""
    tx = _transfer().freeze()
    transaction_hash = tx.get_transaction_hash()
    per_node = tx.get_transaction_hash_per_node()

    assert tx.get_transaction_hash() == transaction_hash
    assert tx.get_transaction_hash_per_node() == per_node

    tx.sign(PrivateKey.generate_ed25519())

    assert tx.get_transaction_hash() != transaction_hash
    assert all(tx.get_transaction_hash_per_node()[node] != per_node[node] for node in NODE_IDS)


def test_transaction_hash_per_node_differs_between_nodes():
    """Test that every node gets its own 48-byte hash."""
    tx = _transfer().freeze().sign(PrivateKey.generate_ecdsa())

    per_node = tx.get_transaction_hash_per_node()

    assert list(per_node) == NODE_IDS
    assert all(len(transaction_hash) == 48 for transaction_hash in per_node.values())
    assert len(set(per_node.values())) == len(NODE_IDS)


def test_transaction_hash_matches_per_node_entry_for_current_node():
    """Test that get_transaction_hash covers the current node, as the request does."""
    tx = _transfer().freeze().sign(PrivateKey.generate_ed25519())

    assert tx.get_transaction_hash() == tx.get_transaction_hash_per_node()[NODE_IDS[0]]

    tx._node_account_ids.advance()

    assert tx.get_transaction_hash() == tx.get_transaction_hash_per_node()[NODE_IDS[1]]


def test_transaction_hash_per_node_covers_current_chunk(file_id):
    """Test that the hash getters cover the current transaction ID of a chunked transaction."""
    tx = _file_append(file_id).freeze()
    first_chunk_hashes = tx.get_transaction_hash_per_node()

    tx._transaction_ids.advance()

    assert tx.get_transaction_hash_per_node() != first_chunk_hashes
    assert tx.get_transaction_hash() == hashlib.sha384(tx._make_request().signedTransactionBytes).digest()


@pytest.mark.parametrize("getter", ["get_transaction_hash", "get_transaction_hash_per_node"])
def test_transaction_hash_requires_frozen_transaction(getter):
    """Test that both hash getters raise on an unfrozen transaction."""
    with pytest.raises(Exception, match="Transaction is not frozen"):
        getattr(_transfer(), getter)()


def test_precomputed_hash_equals_response_hash_of_receiving_node():
    """Test that the hash computed before execute equals TransactionResponse.hash, after a node failover."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)
    response_sequences = [
        [RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable")],
        [ok_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        tx = (
            TransferTransaction()
            .add_hbar_transfer(client.operator_account_id, -1)
            .add_hbar_transfer(AccountId(0, 0, 2), 1)
            .freeze_with(client)
            .sign_with_operator(client)
        )
        per_node = tx.get_transaction_hash_per_node()

        response = tx.execute(client, wait_for_receipt=False)

    assert response.node_id == AccountId(0, 0, 4)
    assert response.hash == per_node[response.node_id]
    assert response.hash != per_node[AccountId(0, 0, 3)]
