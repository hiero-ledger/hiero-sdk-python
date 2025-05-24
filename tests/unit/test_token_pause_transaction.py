import pytest
from unittest.mock import MagicMock

from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, timestamp_pb2, transaction_get_receipt_pb2
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.tokens.token_id import TokenId

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    tx_id = TransactionId(
        valid_start=tx_timestamp,
        account_id=account_id_proto
    )
    return tx_id

def test_builds_token_pause_body_with_correct_token_id(mock_account_ids):
    """
    Given a TokenPauseTransaction with a valid token_id set, when building the
    transaction body, then the inner `tokenPause.token` fields should match.
    """
    account_id, node_account_id, token_id, _ = mock_account_ids

    pause_tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
    )
    
    pause_tx.transaction_id = generate_transaction_id(account_id)
    pause_tx.node_account_id = node_account_id

    transaction_body = pause_tx.build_transaction_body()

    expected = token_id.to_proto()
    assert transaction_body.tokenPause.token == expected

    assert transaction_body.transactionID == pause_tx.transaction_id.to_proto()
    assert transaction_body.nodeAccountID == pause_tx.node_account_id.to_proto()

@pytest.mark.parametrize("bad_token", [None, TokenId(0,0,0)])
def test_build_transaction_body_without_valid_token_id_raises(bad_token):
    """Building a transaction body without a valid token_id must raise ValueError."""
    tx = TokenPauseTransaction()
    if bad_token is not None:
        tx.token_id = bad_token
    with pytest.raises(ValueError):
        tx.build_transaction_body()

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_signed_bytes_include_token_pause_transaction(mock_account_ids, mock_client):
    """Test converting the token pause transaction to protobuf format after signing."""
    account_id, _, token_id, _ = mock_account_ids
    
    pause_tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
    )
    
    pause_tx.transaction_id = generate_transaction_id(account_id)

    pause_key = MagicMock()
    pause_key.sign.return_value = b'signature'
    pause_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    pause_tx.freeze_with(mock_client)

    pause_tx.sign(pause_key)
    proto = pause_tx.to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0

# This test uses fixture mock_account_ids as parameter
def test_pause_transaction_can_execute(mock_account_ids):
    """Test that a pause transaction can be executed successfully."""
    account_id, node_account_id, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful token pause
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
        # Build the transaction
        transaction = (
            TokenPauseTransaction()
            .set_token_id(token_id)
        )
        # Set identifiers so freeze/sign can populate the payload correctly
        transaction.transaction_id = generate_transaction_id(account_id)
        transaction.node_account_id = node_account_id

        # Freeze and sign before execute
        transaction.freeze_with(client)
        dummy_key = MagicMock()
        dummy_key.sign.return_value = b'__SIG__'
        dummy_key.public_key().to_bytes_raw.return_value = b'PUB'
        transaction.sign(dummy_key)
        
        # Execute and assert
        receipt = transaction.execute(client)
        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"