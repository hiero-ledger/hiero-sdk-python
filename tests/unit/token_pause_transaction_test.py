from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.token_pause_pb2 import TokenPauseTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


# This test uses fixture mock_account_ids and token_id as parameter
def test_build_transaction_body(mock_account_ids, token_id):
    """Test building a fungible token pause transaction body with valid values."""
    account_id, _, node_account_id, _, _ = mock_account_ids

    pause_tx = TokenPauseTransaction().set_token_id(token_id)
    pause_tx.operator_account_id = account_id
    pause_tx.set_node_account_ids([node_account_id])

    transaction_body = pause_tx.build_transaction_body()

    assert transaction_body.token_pause.token == token_id._to_proto()

    # Set once node_ids and tx_ids locked on freeze
    assert not transaction_body.HasField("transactionID")
    assert not transaction_body.HasField("nodeAccountID")


def test_build_transaction_body_nft(mock_account_ids, nft_id):
    """Test building an NFT-pause transaction body with valid values."""
    account_id, _, node_account_id, _, _ = mock_account_ids

    # nft_id is NftId(tokenId=TokenId(...), serialNumber=...)
    base_token_id = nft_id.token_id

    pause_tx = TokenPauseTransaction().set_token_id(base_token_id)
    pause_tx.operator_account_id = account_id
    pause_tx.set_node_account_ids([node_account_id])

    transaction_body = pause_tx.build_transaction_body()

    assert transaction_body.token_pause.token == base_token_id._to_proto()

    # Set once node_ids and tx_ids locked on freeze
    assert not transaction_body.HasField("transactionID")
    assert not transaction_body.HasField("nodeAccountID")


# This test uses fixture (token_id, mock_client) as parameter
def test__to_proto(token_id, mock_client):
    """Test converting the token pause transaction to protobuf format after signing."""
    # Build the TokenPauseTransaction
    pause_tx = TokenPauseTransaction().set_token_id(token_id)

    # Create a fake pause key that returns certain bytes when sign() is called:
    pause_key = MagicMock()
    pause_key.sign.return_value = b"signature"
    pause_key.public_key().to_bytes_raw.return_value = b"public_key"

    # Freeze and sign using the pause key, which also generates transaction_id:
    pause_tx.freeze_with(mock_client)
    pause_tx.sign(pause_key)

    # Convert to proto and verify that signedTransactionBytes is non-empty:
    proto = pause_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test__from_proto_restores_token_id():
    """
    _from_proto() must deserialize TokenPauseTransactionBody → .token_id correctly.
    """
    # Construct a TokenPauseTransactionBody protobuf for an example token id.
    proto_body = TokenPauseTransactionBody(token=TokenId(7, 8, 9)._to_proto())

    # Use _from_proto to build a TokenPauseTransaction whose token_id comes from the protobuf just created.
    tx = TokenPauseTransaction()._from_proto(proto_body)

    # Verify that tx.token_id matches TokenId(7, 8, 9)
    assert tx.token_id == TokenId(7, 8, 9)


def test__get_method_points_to_pause_token():
    """_get_method() should return pauseToken as the transaction RPC, and no query RPC."""
    query = TokenPauseTransaction().set_token_id(TokenId(1, 2, 3))

    mock_channel = Mock()
    mock_token_stub = Mock()
    mock_channel.token = mock_token_stub

    method = query._get_method(mock_channel)

    assert method.transaction is mock_token_stub.pauseToken
    assert method.query is None


# This test uses fixture token_id as parameter
def test_pause_transaction_can_execute(token_id):
    """Test that a pause transaction can be executed successfully."""
    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token wipe
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
        transaction = TokenPauseTransaction().set_token_id(token_id)

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"


def test_build_scheduled_body(token_id):
    """Test building a scheduled transaction body for token pause transaction."""
    pause_tx = TokenPauseTransaction().set_token_id(token_id)

    schedulable_body = pause_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("token_pause")
    assert schedulable_body.token_pause.token == token_id._to_proto()


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
    tx = TokenPauseTransaction(token_id=token_id)

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
    tx = TokenPauseTransaction(token_id=token_id)

    restored = _round_trip(tx)

    assert restored.token_id == token_id


def test_from_protobuf_without_specific_body():
    """Retain common fields when the transaction-specific body is absent."""
    body = transaction_pb2.TransactionBody(memo="Common fields only")

    restored = TokenPauseTransaction._from_protobuf(body)

    assert type(restored) is TokenPauseTransaction
    assert restored.memo == "Common fields only"
    assert restored.token_id is None


def test_from_bytes_rejects_invalid_present_token_id():
    """Propagate validation errors for a present but invalid token ID."""
    body = transaction_pb2.TransactionBody()
    body.token_pause.token.tokenNum = -1
    transaction_bytes = transaction_pb2.Transaction(bodyBytes=body.SerializeToString()).SerializeToString()

    with pytest.raises(ValueError, match="Num must be >= 0"):
        Transaction.from_bytes(transaction_bytes)
