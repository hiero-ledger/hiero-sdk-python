from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import SchedulableTransactionBody
from hiero_sdk_python.hapi.services.token_unpause_pb2 import TokenUnpauseTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def test_constructor_without_parameters():
    """Test creating token transaction without constructor parameters."""
    unpause_tx = TokenUnpauseTransaction()
    assert unpause_tx.token_id is None


def test_constructor_with_parameters(mock_account_ids):
    """Test creating token transaction with constructor parameters."""
    _, _, _, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction(token_id=token_id)
    assert unpause_tx.token_id.shard == token_id.shard
    assert unpause_tx.token_id.realm == token_id.realm
    assert unpause_tx.token_id.num == token_id.num


def test_constructor_with_invalid_parameters():
    """Test creating token transaction with invalid constructor parameters."""
    token_id = 100
    with pytest.raises(TypeError, match="token_id must be an instance of TokenId"):
        TokenUnpauseTransaction(token_id=token_id)


def test_build_transaction_body(mock_account_ids):
    """Test building a token unpause transaction body"""
    account_id, _, node_account_id, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction().set_token_id(token_id)
    unpause_tx.set_node_account_ids([node_account_id])
    unpause_tx.operator_account_id = account_id

    transaction_body = unpause_tx.build_transaction_body()

    assert transaction_body.token_unpause.token.shardNum == token_id.shard
    assert transaction_body.token_unpause.token.realmNum == token_id.realm
    assert transaction_body.token_unpause.token.tokenNum == token_id.num


def test_build_transaction_body_when_token_id_not_set(mock_account_ids):
    """Test building a token unpause transaction body without token_id"""
    account_id, _, node_account_id, _, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction()
    unpause_tx.set_node_account_ids([node_account_id])
    unpause_tx.operator_account_id = account_id

    transaction_body = unpause_tx.build_transaction_body()
    assert not transaction_body.token_unpause.HasField("token"), "token field must be unset when token_id is None"


def test_set_method(mock_account_ids):
    """Test the set method of TokenUnpauseTransaction."""
    _, _, _, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction()
    unpause_tx.set_token_id(token_id)

    assert unpause_tx.token_id.shard == token_id.shard
    assert unpause_tx.token_id.realm == token_id.realm
    assert unpause_tx.token_id.num == token_id.num


def test_set_method_with_invalid_parameters():
    """Test the set method of TokenUnpauseTransaction with invalid parameters."""
    token_id = 100
    unpause_tx = TokenUnpauseTransaction()

    with pytest.raises(TypeError, match="token_id must be an instance of TokenId"):
        unpause_tx.set_token_id(token_id)


def test_set_method_require_not_frozen(mock_account_ids, mock_client):
    """Test the set methods of TokenUnpauseTransaction when transaction is freeze."""
    _, _, _, token_id1, token_id2 = mock_account_ids

    unpause_tx = TokenUnpauseTransaction(token_id=token_id1)
    unpause_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        unpause_tx.set_token_id(token_id2)


def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token unpause transaction with a private key."""
    _, _, _, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction()
    unpause_tx.set_token_id(token_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    unpause_tx.freeze_with(mock_client)

    unpause_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = unpause_tx._transaction_body_bytes[unpause_tx.transaction_id][node_id]

    assert len(unpause_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = unpause_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token unpause transaction to protobuf format after signing."""
    _, _, _, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction()
    unpause_tx.set_token_id(token_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    unpause_tx.freeze_with(mock_client)

    unpause_tx.sign(private_key)
    proto = unpause_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token unpause transaction."""
    _, _, _, token_id, _ = mock_account_ids

    unpause_tx = TokenUnpauseTransaction()
    unpause_tx.set_token_id(token_id)

    schedulable_body = unpause_tx.build_scheduled_body()

    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("token_unpause")
    assert schedulable_body.token_unpause.token == token_id._to_proto()


def test_from_proto(mock_account_ids):
    """Test creating a TokenUnpauseTransaction from protobuf representaion."""
    _, _, _, token_id, _ = mock_account_ids

    proto = TokenUnpauseTransactionBody(token=TokenId._to_proto(token_id))
    unpause_tx = TokenUnpauseTransaction._from_proto(proto)

    assert unpause_tx.token_id.shard == token_id.shard
    assert unpause_tx.token_id.realm == token_id.realm
    assert unpause_tx.token_id.num == token_id.num


def test_from_proto_without_token():
    """Test creating a TokenUnpauseTransaction from protobuf representation without token."""
    proto = TokenUnpauseTransactionBody()
    unpause_tx = TokenUnpauseTransaction._from_proto(proto)

    assert unpause_tx.token_id is None, "token_id must remain None when token is absent"


def test_upause_transaction_can_execute(mock_account_ids):
    """Test that a token upause transaction can be executed successfully."""
    _, _, _, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token upause
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = TokenUnpauseTransaction().set_token_id(token_id).freeze_with(client)

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"


def _round_trip(tx, signer=None):
    """Freeze, optionally sign, and deserialize while checking common state."""
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
    """Restore the token ID while retaining signatures and frozen state."""
    token_id = TokenId(1, 2, 345)
    tx = TokenUnpauseTransaction(token_id=token_id)

    restored = _round_trip(tx, signer=private_key if signed else None)

    assert restored.token_id == token_id
    if signed:
        assert restored.is_signed_by(private_key.public_key())
    with pytest.raises(Exception, match="immutable"):
        restored.set_token_id(TokenId(0, 0, 999))


@pytest.mark.parametrize(
    "token_id", [None, TokenId(0, 0, 0), TokenId(1, 2, 345)], ids=["absent-token", "zero-token", "nonzero-token"]
)
def test_from_bytes_preserves_token_presence(token_id):
    """Distinguish an absent token ID from an explicitly present zero ID."""
    tx = TokenUnpauseTransaction(token_id=token_id)

    restored = _round_trip(tx)

    assert restored.token_id == token_id


def test_from_protobuf_without_specific_body():
    """Retain common fields when the transaction-specific body is absent."""
    body = transaction_pb2.TransactionBody(memo="Common fields only")

    restored = TokenUnpauseTransaction._from_protobuf(body)

    assert type(restored) is TokenUnpauseTransaction
    assert restored.memo == "Common fields only"
    assert restored.token_id is None


def test_from_bytes_rejects_invalid_present_token_id():
    """Propagate validation errors for a present but invalid token ID."""
    body = transaction_pb2.TransactionBody()
    body.token_pause.token.tokenNum = -1
    transaction_bytes = transaction_pb2.Transaction(bodyBytes=body.SerializeToString()).SerializeToString()

    with pytest.raises(ValueError, match="Num must be >= 0"):
        Transaction.from_bytes(transaction_bytes)
