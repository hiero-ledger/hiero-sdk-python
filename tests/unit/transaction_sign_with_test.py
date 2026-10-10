"""Unit tests for signer-based signing: sign_with, sign_with_operator and Client.set_operator_with."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from hiero_sdk_python import Signer
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client, Operator
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.hapi.services import transaction_contents_pb2
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit

NODE_IDS = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
PAYER_ID = AccountId(0, 0, 1984)


class RecordingSigner:
    """A signer that wraps a PrivateKey, like an HSM would, and records every call."""

    def __init__(self, private_key: PrivateKey):
        self.private_key = private_key
        self.calls: list[bytes] = []

    def __call__(self, body_bytes: bytes) -> bytes:
        self.calls.append(body_bytes)
        return self.private_key.sign(body_bytes)


def _transfer(payer: AccountId = PAYER_ID) -> TransferTransaction:
    return (
        TransferTransaction()
        .add_hbar_transfer(payer, -1)
        .add_hbar_transfer(AccountId(0, 0, 2), 1)
        .set_transaction_id(TransactionId.generate(payer))
        .set_node_account_ids(NODE_IDS)
    )


def _all_bodies(tx: Transaction) -> list[bytes]:
    return [body for node_bodies in tx._transaction_body_bytes.values() for body in node_bodies.values()]


def _sig_pairs_for(tx: Transaction, body_bytes: bytes, public_key) -> list:
    sig_map = tx._signature_map.get(body_bytes)
    if sig_map is None:
        return []
    return [pair for pair in sig_map.sigPair if pair.pubKeyPrefix == public_key.to_bytes_raw()]


def _assert_signed_once_per_body(tx: Transaction, key: PrivateKey, signer: RecordingSigner):
    bodies = _all_bodies(tx)
    assert signer.calls == bodies

    public_key = key.public_key()
    for body in bodies:
        pairs = _sig_pairs_for(tx, body, public_key)
        assert len(pairs) == 1
        signature = pairs[0].ed25519 if key.is_ed25519() else pairs[0].ECDSA_secp256k1
        public_key.verify(signature, body)


def test_signer_is_exported_from_package_root():
    """Test that Signer is importable from the package root."""
    assert Signer is not None


def test_sign_with_signs_every_body_of_multi_node_transaction():
    """Test that sign_with calls the signer once per node body, with the exact body bytes."""
    key = PrivateKey.generate_ed25519()
    signer = RecordingSigner(key)
    tx = _transfer().freeze()

    tx.sign_with(key.public_key(), signer)

    assert len(_all_bodies(tx)) == len(NODE_IDS)
    _assert_signed_once_per_body(tx, key, signer)


def test_sign_with_signs_every_body_of_chunked_transaction(file_id):
    """Test that sign_with signs every chunk for every node."""
    key = PrivateKey.generate_ed25519()
    signer = RecordingSigner(key)
    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_chunk_size(10)
        .set_contents(b"a" * 30)
        .set_transaction_id(TransactionId.generate(PAYER_ID))
        .set_node_account_ids(NODE_IDS)
        .freeze()
    )

    tx.sign_with(key.public_key(), signer)

    assert len(_all_bodies(tx)) == 3 * len(NODE_IDS)
    _assert_signed_once_per_body(tx, key, signer)


@pytest.mark.parametrize(
    "key, field",
    [
        (PrivateKey.generate_ed25519(), "ed25519"),
        (PrivateKey.generate_ecdsa(), "ECDSA_secp256k1"),
    ],
)
def test_sign_with_uses_signature_field_matching_key_type(key, field):
    """Test that Ed25519 keys populate ed25519 and ECDSA keys populate ECDSA_secp256k1."""
    tx = _transfer().freeze()

    tx.sign_with(key.public_key(), key.sign)

    for body in _all_bodies(tx):
        (pair,) = _sig_pairs_for(tx, body, key.public_key())
        assert pair.WhichOneof("signature") == field


def test_sign_with_same_key_twice_is_noop():
    """Test that signing twice gives one sig pair per body and skips the signer the second time."""
    key = PrivateKey.generate_ed25519()
    signer = RecordingSigner(key)
    tx = _transfer().freeze()

    tx.sign_with(key.public_key(), signer)
    calls_after_first_sign = len(signer.calls)
    tx.sign_with(key.public_key(), signer)
    tx.sign(key)

    assert len(signer.calls) == calls_after_first_sign
    for body in _all_bodies(tx):
        assert len(_sig_pairs_for(tx, body, key.public_key())) == 1


def test_sign_with_requires_frozen_transaction():
    """Test that sign_with raises on an unfrozen transaction, like sign does."""
    key = PrivateKey.generate_ed25519()

    with pytest.raises(Exception, match="Transaction is not frozen"):
        _transfer().sign_with(key.public_key(), key.sign)


def test_sign_with_raising_signer_leaves_transaction_unchanged():
    """Test that a signer failing midway does not leave partial signatures behind."""
    key = PrivateKey.generate_ed25519()
    tx = _transfer().freeze()
    tx.sign(PrivateKey.generate_ed25519())
    before = {body: sig_map.SerializeToString() for body, sig_map in tx._signature_map.items()}

    calls = []

    def flaky_signer(body_bytes: bytes) -> bytes:
        calls.append(body_bytes)
        if len(calls) == 2:
            raise RuntimeError("HSM unavailable")
        return key.sign(body_bytes)

    with pytest.raises(RuntimeError, match="HSM unavailable"):
        tx.sign_with(key.public_key(), flaky_signer)

    assert {body: sig_map.SerializeToString() for body, sig_map in tx._signature_map.items()} == before
    assert not tx._signers[1:]


def test_sign_with_rejects_non_bytes_signature():
    """Test that a signer returning something other than bytes raises TypeError."""
    key = PrivateKey.generate_ed25519()
    tx = _transfer().freeze()

    with pytest.raises(TypeError, match="signer must return bytes"):
        tx.sign_with(key.public_key(), lambda body_bytes: key.sign(body_bytes).hex())

    assert tx._signature_map == {}


def test_sign_with_rejects_non_callable_signer():
    """Test that sign_with raises TypeError when the signer is not callable."""
    key = PrivateKey.generate_ed25519()

    with pytest.raises(TypeError, match="signer must be callable"):
        _transfer().freeze().sign_with(key.public_key(), b"not a signer")


def test_sign_with_on_restored_transaction_dedups_and_adds():
    """Test that restored signatures are deduplicated and new ones are added after from_bytes."""
    restored_key = PrivateKey.generate_ed25519()
    new_key = PrivateKey.generate_ecdsa()
    tx = _transfer().set_node_account_ids([NODE_IDS[0]]).freeze().sign(restored_key)

    restored = Transaction.from_bytes(tx.to_bytes())
    restored_signer = RecordingSigner(restored_key)
    new_signer = RecordingSigner(new_key)

    restored.sign_with(restored_key.public_key(), restored_signer)
    restored.sign_with(new_key.public_key(), new_signer)

    assert restored_signer.calls == []
    (body,) = _all_bodies(restored)
    assert len(_sig_pairs_for(restored, body, restored_key.public_key())) == 1
    assert len(_sig_pairs_for(restored, body, new_key.public_key())) == 1


def test_sign_registers_signer():
    """Test that sign() routes through sign_with and registers the key's signer."""
    key = PrivateKey.generate_ecdsa()
    tx = _transfer().freeze()

    tx.sign(key)

    assert tx.is_signed_by(key.public_key())
    assert [pk.to_bytes_raw() for pk, _ in tx._signers] == [key.public_key().to_bytes_raw()]


def test_apply_signers_signs_rebuilt_bodies():
    """Test that _apply_signers re-signs bodies that lack a signature from a registered signer."""
    key = PrivateKey.generate_ed25519()
    signer = RecordingSigner(key)
    tx = _transfer().freeze().sign_with(key.public_key(), signer)

    rebuilt_tx_id = TransactionId.generate(PAYER_ID)
    rebuilt_body = b"rebuilt body bytes"
    tx._transaction_body_bytes[rebuilt_tx_id] = {NODE_IDS[0]: rebuilt_body}
    signer.calls.clear()

    tx._apply_signers()

    assert signer.calls == [rebuilt_body]
    assert len(_sig_pairs_for(tx, rebuilt_body, key.public_key())) == 1


def test_sign_with_operator_requires_operator():
    """Test that sign_with_operator raises when the client has no operator."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="Client must have an operator"):
        _transfer().freeze().sign_with_operator(client)

    client.close()


def test_sign_with_operator_freezes_unfrozen_transaction(mock_client):
    """Test that sign_with_operator freezes the transaction with the client first."""
    tx = TransferTransaction().add_hbar_transfer(PAYER_ID, -1).add_hbar_transfer(AccountId(0, 0, 2), 1)

    tx.sign_with_operator(mock_client)

    assert tx._transaction_body_bytes
    assert tx.is_signed_by(mock_client.operator_private_key.public_key())


def test_sign_with_operator_uses_signer_based_operator(mock_client):
    """Test that sign_with_operator signs through the operator's signer callback."""
    key = PrivateKey.generate_ecdsa()
    signer = RecordingSigner(key)
    mock_client.set_operator_with(PAYER_ID, key.public_key(), signer)
    tx = _transfer().freeze()

    tx.sign_with_operator(mock_client)

    _assert_signed_once_per_body(tx, key, signer)


def test_set_operator_populates_private_key_and_operator():
    """Test that set_operator stays backward compatible and returns the client."""
    client = Client.for_testnet()
    key = PrivateKey.generate_ed25519()

    assert client.set_operator(PAYER_ID, key) is client

    assert client.operator_private_key is key
    assert client.operator_public_key.to_bytes_raw() == key.public_key().to_bytes_raw()
    assert client.operator.account_id == PAYER_ID
    assert client.operator.private_key is key
    assert client.operator.signer(b"data") == key.sign(b"data")

    client.close()


def test_set_operator_with_leaves_private_key_none():
    """Test that set_operator_with stores the public key and signer, with no private key."""
    client = Client.for_testnet()
    key = PrivateKey.generate_ed25519()
    client.set_operator(AccountId(0, 0, 1), PrivateKey.generate_ed25519())

    assert client.set_operator_with(PAYER_ID, key.public_key(), key.sign) is client

    assert client.operator_private_key is None
    assert client.operator_signer == key.sign
    assert client.operator == Operator(PAYER_ID, None, key.public_key(), key.sign)

    client.close()


def test_operator_supports_positional_construction():
    """Test that Operator keeps working when built with account ID and private key only."""
    key = PrivateKey.generate_ed25519()

    operator = Operator(PAYER_ID, key)

    assert operator.private_key is key
    assert operator.public_key is None
    assert operator.signer is None


def test_operator_private_key_assigned_directly_still_signs():
    """Test that assigning operator_private_key directly still yields a usable operator."""
    client = Client.for_testnet()
    key = PrivateKey.generate_ed25519()

    client.operator_account_id = PAYER_ID
    client.operator_private_key = key

    assert client.operator.public_key.to_bytes_raw() == key.public_key().to_bytes_raw()
    assert client.operator.signer(b"data") == key.sign(b"data")

    client.close()


def test_execute_signs_with_operator_when_operator_is_payer(mock_client):
    """Test that execute adds the operator signature when the operator pays."""
    tx = _transfer(payer=mock_client.operator_account_id)

    with patch.object(Transaction, "_execute", return_value=TransactionResponse()):
        tx.execute(mock_client, wait_for_receipt=False)

    assert tx.is_signed_by(mock_client.operator_private_key.public_key())


def test_execute_skips_operator_signature_when_operator_is_not_payer(mock_client):
    """Test that execute does not add the operator signature for another payer."""
    payer_key = PrivateKey.generate_ed25519()
    tx = _transfer(payer=AccountId(0, 0, 5555)).freeze_with(mock_client).sign(payer_key)

    with patch.object(Transaction, "_execute", return_value=TransactionResponse()):
        tx.execute(mock_client, wait_for_receipt=False)

    assert tx.is_signed_by(payer_key.public_key())
    for body in _all_bodies(tx):
        assert _sig_pairs_for(tx, body, mock_client.operator_private_key.public_key()) == []


def test_execute_without_operator_does_not_crash(mock_client):
    """Test that a fully signed transaction can be submitted from an operator-less client."""
    payer_key = PrivateKey.generate_ed25519()
    tx = _transfer().freeze().sign(payer_key)
    mock_client.operator_account_id = None
    mock_client.operator_private_key = None

    with patch.object(Transaction, "_execute", return_value=TransactionResponse()):
        tx.execute(mock_client, wait_for_receipt=False)

    for body in _all_bodies(tx):
        assert len(tx._signature_map[body].sigPair) == 1


def test_execute_signs_with_signer_based_operator(mock_client):
    """Test that execute signs through the operator's signer callback."""
    key = PrivateKey.generate_ecdsa()
    signer = RecordingSigner(key)
    mock_client.set_operator_with(PAYER_ID, key.public_key(), signer)
    tx = _transfer(payer=PAYER_ID)

    with patch.object(Transaction, "_execute", return_value=TransactionResponse()):
        tx.execute(mock_client, wait_for_receipt=False)

    _assert_signed_once_per_body(tx, key, signer)


def test_batchify_signs_with_signer_based_operator(mock_client):
    """Test that batchify signs through the operator's signer callback."""
    key = PrivateKey.generate_ed25519()
    signer = RecordingSigner(key)
    mock_client.set_operator_with(PAYER_ID, key.public_key(), signer)

    tx = (
        TransferTransaction()
        .add_hbar_transfer(PAYER_ID, -1)
        .add_hbar_transfer(AccountId(0, 0, 2), 1)
        .batchify(mock_client, PrivateKey.generate_ed25519())
    )

    _assert_signed_once_per_body(tx, key, signer)


def _payment_signature_pair(query: TokenInfoQuery):
    header = query._make_request_header()
    assert header.HasField("payment")

    signed_transaction = transaction_contents_pb2.SignedTransaction()
    signed_transaction.ParseFromString(header.payment.signedTransactionBytes)
    (pair,) = signed_transaction.sigMap.sigPair
    return signed_transaction.bodyBytes, pair


def test_query_payment_signs_with_signer_based_operator(mock_client):
    """Test that query payment is signed through the operator's signer callback."""
    key = PrivateKey.generate_ecdsa()
    signer = RecordingSigner(key)
    mock_client.set_operator_with(PAYER_ID, key.public_key(), signer)

    query = TokenInfoQuery().set_node_account_ids([NODE_IDS[0]])
    query.operator = mock_client.operator
    query.payment_amount = Hbar(1)

    body_bytes, pair = _payment_signature_pair(query)

    assert signer.calls == [body_bytes]
    assert pair.pubKeyPrefix == key.public_key().to_bytes_raw()
    key.public_key().verify(pair.ECDSA_secp256k1, body_bytes)


def test_query_payment_supports_private_key_only_operator():
    """Test that query payment still works with an Operator built from a private key only."""
    key = PrivateKey.generate_ed25519()

    query = TokenInfoQuery().set_node_account_ids([NODE_IDS[0]])
    query.operator = Operator(PAYER_ID, key)
    query.payment_amount = Hbar(1)

    body_bytes, pair = _payment_signature_pair(query)

    assert pair.pubKeyPrefix == key.public_key().to_bytes_raw()
    key.public_key().verify(pair.ed25519, body_bytes)
