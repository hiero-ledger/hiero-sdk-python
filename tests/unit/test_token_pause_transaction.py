import pytest
from unittest.mock import MagicMock, Mock

from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.hapi.services.token_pause_pb2 import TokenPauseTransactionBody
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

@pytest.fixture
def built_pause_tx(mock_account_ids, mock_client, generate_transaction_id):
    """
    Factory: returns a TokenPauseTransaction (set, frozen, signed) given a pause_key.
    Usage: tx = built_pause_tx(pause_key)
    """
    sender, _, node_account, fungible_token, _ = mock_account_ids

    def _make(pause_key):
        tx = TokenPauseTransaction().set_token_id(fungible_token)
        tx.transaction_id  = generate_transaction_id(sender)
        tx.node_account_id = node_account
        tx.freeze_with(mock_client)
        tx.sign(pause_key)
        return tx

    return _make

@pytest.fixture
def test_builds_token_pause_body_with_correct_ids(mock_account_ids, generate_transaction_id):
    """
    build_transaction_body() should embed:
      - tokenPause.token   == token_id.to_proto()
      - transactionID      == transaction_id.to_proto()
      - nodeAccountID      == node_account_id.to_proto()
    """
    sender, _, node_account, token_id, _ = mock_account_ids

    tx = TokenPauseTransaction().set_token_id(token_id)
    tx.transaction_id  = generate_transaction_id(sender)
    tx.node_account_id = node_account

    body = tx.build_transaction_body()

    assert body.tokenPause.token  == token_id.to_proto()
    assert body.transactionID     == tx.transaction_id.to_proto()
    assert body.nodeAccountID     == tx.node_account_id.to_proto()

@pytest.mark.parametrize("bad_token", [None, TokenId(0, 0, 0)])
def test_build_transaction_body_without_valid_token_id_raises(bad_token):
    """
    If token_id is missing or zero, build_transaction_body() must raise ValueError.
    """
    tx = TokenPauseTransaction()
    if bad_token is not None:
        tx.token_id = bad_token

    with pytest.raises(ValueError, match="token_id must be set"):
        tx.build_transaction_body()

def test__get_method_points_to_pause_token():
    """_get_method() should return pauseToken as the transaction RPC, and no query RPC."""
    query = TokenPauseTransaction().set_token_id(TokenId(1, 2, 3))

    mock_channel    = Mock()
    mock_token_stub = Mock()
    mock_channel.token = mock_token_stub

    method = query._get_method(mock_channel)

    assert method.transaction is mock_token_stub.pauseToken
    assert method.query       is None

def test__from_proto_restores_token_id():
    """
    _from_proto() must deserialize TokenPauseTransactionBody → .token_id correctly.
    """
    proto_body = TokenPauseTransactionBody(
        token=TokenId(7, 8, 9).to_proto()
    )
    tx = TokenPauseTransaction()._from_proto(proto_body)

    assert tx.token_id == TokenId(7, 8, 9)


def test_signed_bytes_include_token_pause_transaction(built_pause_tx):
    """
    After freeze() and sign(pause_key), to_proto() must produce non-empty
    signedTransactionBytes.
    """
    pause_key = MagicMock()
    pause_key.sign.return_value = b'__FAKE_SIG__'
    fake_pub = pause_key.public_key()
    fake_pub.to_bytes_raw.return_value = b'__FAKE_PUB__'

    tx = built_pause_tx(pause_key)
    proto = tx.to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_pause_transaction_can_execute(mock_account_ids, generate_transaction_id):
    """
    A well-formed & signed TokenPauseTransaction against the mock server
    should return a SUCCESS receipt.
    """
    sender, _, node_account, fungible_token, _ = mock_account_ids

    # 1) Precheck OK
    ok_resp = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    # 2) Receipt SUCCESS
    success_receipt = TransactionReceiptProto(status=ResponseCode.SUCCESS)
    receipt_query = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=success_receipt
        )
    )

    response_sequences = [
        [ok_resp, receipt_query],
    ]
    with mock_hedera_servers(response_sequences) as client:        
        tx = TokenPauseTransaction().set_token_id(fungible_token)
        tx.transaction_id  = generate_transaction_id(sender)
        tx.node_account_id = node_account

        tx.freeze_with(client)
        fake_priv = MagicMock()
        fake_priv.sign.return_value = b'__SIG__'
        fake_pub = fake_priv.public_key()
        fake_pub.to_bytes_raw.return_value = b'PUB'
        tx.sign(fake_priv)

        receipt = tx.execute(client)
        assert receipt.status == ResponseCode.SUCCESS