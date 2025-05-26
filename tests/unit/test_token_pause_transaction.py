import time
import pytest
from unittest.mock import MagicMock

from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    timestamp_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

@pytest.fixture
def built_pause_tx(mock_account_ids, mock_client, generate_transaction_id):
    """
    Factory fixture: given a pause_key, returns a TokenPauseTransaction
    that’s already set up, frozen, and signed with that key.
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


def test_builds_token_pause_body_with_correct_ids(mock_account_ids, generate_transaction_id):
    """
    build_transaction_body() should embed:
      - tokenPause.token   == token_id.to_proto()
      - transactionID      == transaction_id.to_proto()
      - nodeAccountID      == node_account_id.to_proto()
    """
    sender, _, node_account, token_id, _ = mock_account_ids

    pause_tx = TokenPauseTransaction().set_token_id(token_id)
    pause_tx.transaction_id  = generate_transaction_id(sender)
    pause_tx.node_account_id = node_account

    body = pause_tx.build_transaction_body()

    assert body.tokenPause.token  == token_id.to_proto()
    assert body.transactionID         == pause_tx.transaction_id.to_proto()
    assert body.nodeAccountID         == pause_tx.node_account_id.to_proto()


@pytest.mark.parametrize("bad_token", [None, TokenId(0, 0, 0)])
def test_build_transaction_body_without_valid_token_id_raises(bad_token):
    """
    If token_id is missing or zero, build_transaction_body() must ValueError.
    """
    pause_tx = TokenPauseTransaction()
    if bad_token is not None:
        pause_tx.token_id = bad_token

    with pytest.raises(ValueError, match="token_id must be set"):
        pause_tx.build_transaction_body()

def test_signed_bytes_include_token_pause_transaction(built_pause_tx):
    """
    After freeze() and sign(pause_key), to_proto() must embed a non-empty
    signedTransactionBytes blob.
    """
    # Arrange: stub pause key + public key
    pause_key = MagicMock()
    pause_key.sign.return_value = b'__FAKE_SIG__'

    fake_pub = pause_key.public_key()
    fake_pub.to_bytes_raw.return_value = b'__FAKE_PUB__'

    # Act
    pause_tx = built_pause_tx(pause_key)
    proto = pause_tx.to_proto()

    # Assert
    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0

def test_pause_transaction_can_execute(mock_account_ids):
    """
    A properly built & signed TokenPauseTransaction against a mock server
    should return a SUCCESS receipt.
    """
    sender, _, node_account, fungible_token, _ = mock_account_ids

    # 1) Precheck-ok response
    ok_resp = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    # 2) Receipt SUCCESS response
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
        pause_tx = TokenPauseTransaction().set_token_id(fungible_token)
        pause_tx.transaction_id  = TransactionId.generate(sender)
        pause_tx.node_account_id = node_account

        pause_tx.freeze_with(client)

        dummy_priv_key = MagicMock()
        dummy_priv_key.sign.return_value = b'__SIG__'
        
        dummy_pub_key = dummy_priv_key.public_key()
        dummy_pub_key.to_bytes_raw.return_value = b'PUB'

        pause_tx.sign(dummy_priv_key)

        receipt = pause_tx.execute(client)
        assert receipt.status == ResponseCode.SUCCESS


