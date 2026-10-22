from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit

ACCOUNT_TRANSACTIONS = [
    TokenFreezeTransaction,
    TokenUnfreezeTransaction,
    TokenGrantKycTransaction,
    TokenRevokeKycTransaction,
]

TOKEN_TRANSACTIONS = [
    TokenPauseTransaction,
    TokenUnpauseTransaction,
]

ALL_TRANSACTIONS = ACCOUNT_TRANSACTIONS + TOKEN_TRANSACTIONS


def _round_trip(tx, signer=None):
    """Serialize and restore a frozen transaction, checking common state."""
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


@pytest.mark.parametrize("transaction_class", ALL_TRANSACTIONS)
@pytest.mark.parametrize("signed", [False, True], ids=["unsigned", "signed"])
def test_from_bytes_restores_all_fields(transaction_class, signed, private_key):
    """Restore populated IDs while retaining signatures and frozen state."""
    token_id = TokenId(1, 2, 345)
    account_id = AccountId(4, 5, 678)

    kwargs = {"token_id": token_id}
    if transaction_class in ACCOUNT_TRANSACTIONS:
        kwargs["account_id"] = account_id

    tx = transaction_class(**kwargs)
    restored = _round_trip(tx, signer=private_key if signed else None)

    assert restored.token_id == token_id
    if transaction_class in ACCOUNT_TRANSACTIONS:
        assert restored.account_id == account_id

    if signed:
        assert restored.is_signed_by(private_key.public_key())

    with pytest.raises(Exception, match="immutable"):
        restored.set_token_id(TokenId(0, 0, 999))


@pytest.mark.parametrize("transaction_class", ACCOUNT_TRANSACTIONS)
@pytest.mark.parametrize(
    "token_id",
    [None, TokenId(0, 0, 0), TokenId(1, 2, 345)],
    ids=["absent-token", "zero-token", "nonzero-token"],
)
@pytest.mark.parametrize(
    "account_id",
    [None, AccountId(), AccountId(4, 5, 678)],
    ids=["absent-account", "zero-account", "nonzero-account"],
)
def test_from_bytes_preserves_token_and_account_presence(transaction_class, token_id, account_id):
    """Distinguish absent IDs from explicitly present zero-valued IDs."""
    tx = transaction_class(token_id=token_id, account_id=account_id)

    restored = _round_trip(tx)

    assert restored.token_id == token_id
    assert restored.account_id == account_id


@pytest.mark.parametrize("transaction_class", TOKEN_TRANSACTIONS)
@pytest.mark.parametrize(
    "token_id",
    [None, TokenId(0, 0, 0), TokenId(1, 2, 345)],
    ids=["absent-token", "zero-token", "nonzero-token"],
)
def test_from_bytes_preserves_token_presence(transaction_class, token_id):
    """Preserve token presence for pause and unpause."""
    restored = _round_trip(transaction_class(token_id=token_id))

    assert restored.token_id == token_id


@pytest.mark.parametrize("transaction_class", ACCOUNT_TRANSACTIONS)
@pytest.mark.parametrize("alias_kind", ["key", "evm"])
def test_from_bytes_preserves_account_alias(transaction_class, alias_kind, private_key):
    """Restore alias-based accounts through the SDK's AccountId converter."""
    if alias_kind == "key":
        account_id = AccountId(4, 5, alias_key=private_key.public_key())
    else:
        account_id = AccountId(
            4,
            5,
            evm_address=EvmAddress.from_bytes(bytes.fromhex("12" * 20)),
        )
    tx = transaction_class(token_id=TokenId(1, 2, 345), account_id=account_id)

    restored = _round_trip(tx)

    assert restored.account_id == account_id


@pytest.mark.parametrize("transaction_class", ALL_TRANSACTIONS)
def test_from_protobuf_without_specific_body(transaction_class):
    """Retain common fields when the transaction-specific body is absent."""
    body = transaction_pb2.TransactionBody(memo="Common fields only")

    restored = transaction_class._from_protobuf(body)

    assert type(restored) is transaction_class
    assert restored.memo == "Common fields only"
    assert restored.token_id is None
    if transaction_class in ACCOUNT_TRANSACTIONS:
        assert restored.account_id is None


@pytest.mark.parametrize(
    "body_field",
    [
        "tokenFreeze",
        "tokenUnfreeze",
        "tokenGrantKyc",
        "tokenRevokeKyc",
        "token_pause",
        "token_unpause",
    ],
)
def test_from_bytes_rejects_invalid_present_token_id(body_field):
    """Propagate TokenId validation instead of silently ignoring invalid IDs."""
    body = transaction_pb2.TransactionBody()
    getattr(body, body_field).token.tokenNum = -1

    transaction_bytes = transaction_pb2.Transaction(bodyBytes=body.SerializeToString()).SerializeToString()

    with pytest.raises(ValueError, match="Num must be >= 0"):
        Transaction.from_bytes(transaction_bytes)
