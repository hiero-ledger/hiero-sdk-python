from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.hapi.services import timestamp_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit


def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time

    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)
    return TransactionId(valid_start=tx_timestamp, account_id=account_id_proto)


def test_build_transaction_body(mock_account_ids):
    """Test building the token unfreeze transaction body with valid account ID and token ID."""
    account_id, freeze_id, node_account_id, token_id, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)
    unfreeze_tx.set_node_account_ids([node_account_id])
    transaction_body = unfreeze_tx.build_transaction_body()

    assert transaction_body.tokenUnfreeze.token.shardNum == 1
    assert transaction_body.tokenUnfreeze.token.realmNum == 1
    assert transaction_body.tokenUnfreeze.token.tokenNum == 1

    proto_account = freeze_id._to_proto()
    assert transaction_body.tokenUnfreeze.account == proto_account


def test_missing_token_id(mock_account_ids):
    """Test that building the protobuf body without TokenID ignores the missing ID."""
    _, freeze_id, _, _, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_account_id(freeze_id)

    body = unfreeze_tx._build_proto_body()

    assert not body.HasField("token")
    assert body.account == freeze_id._to_proto()


def test_missing_account_id(mock_account_ids):
    """Test that building the protobuf body without AccountID ignores the missing ID."""
    _, _, _, token_id, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)

    body = unfreeze_tx._build_proto_body()

    assert not body.HasField("account")
    assert body.token == token_id._to_proto()


def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token unfreeze transaction with a freeze key."""
    account_id, freeze_id, _, token_id, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b"signature"
    freeze_key.public_key().to_bytes_raw.return_value = b"public_key"

    unfreeze_tx.freeze_with(mock_client)

    unfreeze_tx.sign(freeze_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = unfreeze_tx._transaction_body_bytes[unfreeze_tx.transaction_id][node_id]

    assert len(unfreeze_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = unfreeze_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token unfreeze transaction."""
    _, freeze_id, _, token_id, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)

    schedulable_body = unfreeze_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenUnfreeze")
    assert schedulable_body.tokenUnfreeze.token == token_id._to_proto()
    assert schedulable_body.tokenUnfreeze.account == freeze_id._to_proto()


def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token unfreeze transaction to protobuf format after signing."""
    account_id, freeze_id, _, token_id, _ = mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b"signature"
    freeze_key.public_key().to_bytes_raw.return_value = b"mock_pubkey"

    unfreeze_tx.freeze_with(mock_client)

    unfreeze_tx.sign(freeze_key)
    proto = unfreeze_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def _round_trip(tx, signer=None):
    tx.set_transaction_id(TransactionId.from_string("0.0.123@1800000000.123456789"))
    tx.set_node_account_ids([AccountId(0, 0, 3)])
    tx.set_transaction_memo("Deserialization regression")
    tx.set_transaction_valid_duration(90)
    tx.transaction_fee = 123_456_789
    tx.freeze()

    if signer is not None:
        tx.sign(signer)

    original_bytes = tx.to_bytes()
    restored = Transaction.from_bytes(original_bytes)

    assert type(restored) is type(tx)
    assert restored.to_bytes() == original_bytes
    assert restored.transaction_id == tx.transaction_id
    assert restored.memo == "Deserialization regression"
    assert restored.transaction_valid_duration == 90
    assert restored.transaction_fee == 123_456_789

    return restored


@pytest.mark.parametrize("signed", [False, True], ids=["unsigned", "signed"])
def test_from_bytes_restores_all_fields(signed, private_key):
    """Restore populated IDs while retaining signatures and frozen state."""
    token_id = TokenId(1, 2, 345)
    account_id = AccountId(4, 5, 678)

    tx = TokenUnfreezeTransaction(token_id=token_id, account_id=account_id)
    restored = _round_trip(tx, signer=private_key if signed else None)

    assert restored.token_id == token_id
    assert restored.account_id == account_id

    if signed:
        assert restored.is_signed_by(private_key.public_key())

    with pytest.raises(Exception, match="immutable"):
        restored.set_token_id(TokenId(0, 0, 999))


@pytest.mark.parametrize(
    "token_id", [None, TokenId(0, 0, 0), TokenId(1, 2, 345)], ids=["absent-token", "zero-token", "nonzero-token"]
)
@pytest.mark.parametrize(
    "account_id", [None, AccountId(), AccountId(4, 5, 678)], ids=["absent-account", "zero-account", "nonzero-account"]
)
def test_from_bytes_preserves_token_and_account_presence(token_id, account_id):
    """Distinguish absent IDs from explicitly present zero-valued IDs."""
    tx = TokenUnfreezeTransaction(token_id=token_id, account_id=account_id)

    restored = _round_trip(tx)

    assert restored.token_id == token_id
    assert restored.account_id == account_id


@pytest.mark.parametrize("alias_kind", ["key", "evm"])
def test_from_bytes_preserves_account_alias(private_key, alias_kind):
    """Preserve public-key and EVM-address account aliases."""
    if alias_kind == "key":
        account_id = AccountId(4, 5, alias_key=private_key.public_key())
    else:
        account_id = AccountId(4, 5, evm_address=EvmAddress.from_bytes(bytes.fromhex("12" * 20)))

    tx = TokenUnfreezeTransaction(token_id=TokenId(1, 2, 345), account_id=account_id)

    restored = _round_trip(tx)

    assert restored.account_id == account_id


def test_from_protobuf_without_specific_body():
    """Retain common fields when the transaction-specific body is absent."""
    body = transaction_pb2.TransactionBody(memo="Common fields only")

    restored = TokenUnfreezeTransaction._from_protobuf(body)

    assert type(restored) is TokenUnfreezeTransaction
    assert restored.memo == "Common fields only"
    assert restored.token_id is None
    assert restored.account_id is None


def test_from_bytes_rejects_invalid_present_token_id():
    """Propagate validation errors for a present but invalid token ID."""
    body = transaction_pb2.TransactionBody()
    body.tokenFreeze.token.tokenNum = -1

    transaction_bytes = transaction_pb2.Transaction(bodyBytes=body.SerializeToString()).SerializeToString()

    with pytest.raises(ValueError, match="Num must be >= 0"):
        Transaction.from_bytes(transaction_bytes)
