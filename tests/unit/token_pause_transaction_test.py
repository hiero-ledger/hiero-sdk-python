import pytest
from unittest.mock import MagicMock, Mock


from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hapi.services.token_pause_pb2 import TokenPauseTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId

from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture mock_account_ids and token_id as parameter
def test_build_transaction_body(mock_account_ids, token_id):
    """Test building a fungible token pause transaction body with valid values."""
    account_id, _, node_account_id, _, _ = mock_account_ids

    pause_tx = TokenPauseTransaction().set_token_id(token_id)
    pause_tx.operator_account_id = account_id
    pause_tx.node_account_id = node_account_id

    transaction_body = pause_tx.build_transaction_body() # Will generate a transaction_id

    assert transaction_body.token_pause.token  == token_id._to_proto()
    assert transaction_body.transactionID     == pause_tx.transaction_id._to_proto()
    assert transaction_body.nodeAccountID     == pause_tx.node_account_id._to_proto()

def test_build_transaction_body_nft(mock_account_ids, nft_id):
    """Test building an NFT‐pause transaction body with valid values."""
    account_id, _, node_account_id, _, _ = mock_account_ids

    # nft_id is NftId(tokenId=TokenId(...), serialNumber=...)
    base_token_id = nft_id.token_id

    pause_tx = TokenPauseTransaction().set_token_id(base_token_id)
    pause_tx.operator_account_id = account_id
    pause_tx.node_account_id = node_account_id

    transaction_body = pause_tx.build_transaction_body()

    assert transaction_body.token_pause.token == base_token_id._to_proto()
    assert transaction_body.transactionID    == pause_tx.transaction_id._to_proto()
    assert transaction_body.nodeAccountID    == pause_tx.node_account_id._to_proto()

# This test uses fixture (token_id, mock_client) as parameter
def test__to_proto(token_id, mock_client):
    """Test converting the token pause transaction to protobuf format after signing."""
    
    # Build the TokenPauseTransaction 
    pause_tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
    )
    
    # Create a fake pause key that returns certain bytes when sign() is called:
    pause_key = MagicMock()
    pause_key.sign.return_value = b'signature'
    pause_key.public_key().to_bytes_raw.return_value = b'public_key'
    
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

# This test uses fixture token_id as parameter
def test_pause_transaction_can_execute(token_id):
    """Test that a pause transaction can be executed successfully."""

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful token wipe
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS
    )
    
    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto
        )
    )
    
    response_sequences = [
        [ok_response, receipt_query_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client:
        transaction = (
            TokenPauseTransaction()
            .set_token_id(token_id)
        )
        
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