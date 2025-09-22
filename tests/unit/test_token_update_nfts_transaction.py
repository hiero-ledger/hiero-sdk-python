import pytest

from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.token_update_nfts_pb2 import TokenUpdateNftsTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_update_nfts_transaction import TokenUpdateNftsTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from google.protobuf.wrappers_pb2 import BytesValue
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_build_transaction_body(mock_account_ids):
    """Test building a token update NFTs transaction body with valid values."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'updated metadata'
    
    update_tx = (
        TokenUpdateNftsTransaction()
        .set_token_id(token_id)
        .set_serial_numbers(serial_numbers)
        .set_metadata(metadata)
    )
    
    # Set operator and node account IDs needed for building transaction body
    update_tx.operator_account_id = operator_id
    update_tx.node_account_id = node_account_id
    transaction_body = update_tx.build_transaction_body()
    
    assert transaction_body.token_update_nfts.token.shardNum == token_id.shard
    assert transaction_body.token_update_nfts.token.realmNum == token_id.realm
    assert transaction_body.token_update_nfts.token.tokenNum == token_id.num
    assert transaction_body.token_update_nfts.serial_numbers == serial_numbers
    assert transaction_body.token_update_nfts.metadata.value == metadata

def test_build_transaction_body_validation_errors(mock_account_ids):
    """Test that build_transaction_body raises appropriate validation errors."""
    _, _, _, token_id, _ = mock_account_ids
    
    # Test missing token_id
    update_tx = TokenUpdateNftsTransaction()
    
    with pytest.raises(ValueError, match="Missing token ID"):
        update_tx.build_transaction_body()
        
    # Test missing serial numbers
    update_tx = TokenUpdateNftsTransaction(
        token_id=token_id,
    )
    
    with pytest.raises(ValueError, match="Missing serial numbers"):
        update_tx.build_transaction_body()
    
    # Test metadata too large
    update_tx = TokenUpdateNftsTransaction(
        token_id=token_id,
        serial_numbers=[1],
        metadata=b'x' * 101  # 101 bytes
    )
    
    with pytest.raises(ValueError, match="Metadata must be less than 100 bytes"):
        update_tx.build_transaction_body()

def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token update NFTs transaction with constructor parameters."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'new metadata'

    update_tx = TokenUpdateNftsTransaction(
        token_id=token_id,
        serial_numbers=serial_numbers,
        metadata=metadata
    )

    assert update_tx.token_id == token_id
    assert update_tx.serial_numbers == serial_numbers
    assert update_tx.metadata == metadata

def test_set_methods(mock_account_ids):
    """Test the set methods of TokenUpdateNftsTransaction."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'new metadata'

    update_tx = TokenUpdateNftsTransaction()
    
    # Test method chaining
    tx_after_set = update_tx.set_token_id(token_id)
    assert tx_after_set is update_tx
    assert update_tx.token_id == token_id
    
    tx_after_set = update_tx.set_serial_numbers(serial_numbers)
    assert tx_after_set is update_tx
    assert update_tx.serial_numbers == serial_numbers
    
    tx_after_set = update_tx.set_metadata(metadata)
    assert tx_after_set is update_tx
    assert update_tx.metadata == metadata

def test_set_methods_require_not_frozen(mock_account_ids, mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'new metadata'

    update_tx = TokenUpdateNftsTransaction(
        token_id=token_id,
        serial_numbers=serial_numbers,
    )
    update_tx.freeze_with(mock_client)
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        update_tx.set_token_id(token_id)
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        update_tx.set_serial_numbers(serial_numbers)
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        update_tx.set_metadata(metadata)

def test_update_nfts_transaction_can_execute(mock_account_ids):
    """Test that a token update NFTs transaction can be executed successfully."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'updated metadata'

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful token update NFTs
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
            TokenUpdateNftsTransaction()
            .set_token_id(token_id)
            .set_serial_numbers(serial_numbers)
            .set_metadata(metadata)
        )
        
        receipt = transaction.execute(client)
        
        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"

def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token update NFTs transaction."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata = b'updated metadata'
    
    update_tx = (
        TokenUpdateNftsTransaction()
        .set_token_id(token_id)
        .set_serial_numbers(serial_numbers)
        .set_metadata(metadata)
    )
    
    schedulable_body = update_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("token_update_nfts")
    assert schedulable_body.token_update_nfts.token == token_id._to_proto()
    assert schedulable_body.token_update_nfts.serial_numbers == serial_numbers
    assert schedulable_body.token_update_nfts.metadata.value == metadata

def test_update_nfts_transaction_from_proto(mock_account_ids):
    """Test that a token update NFTs transaction can be created from a protobuf object."""
    _, _, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]
    metadata_bytes = b'updated metadata'
    
    # Create protobuf object for token update NFTs transaction
    proto = TokenUpdateNftsTransactionBody(
        token=token_id._to_proto(),
        serial_numbers=serial_numbers,
        metadata=BytesValue(value=metadata_bytes)
    )
    
    # Deserialize the protobuf object
    _from_proto = TokenUpdateNftsTransaction()._from_proto(proto)
    
    # Verify deserialized transaction matches original data
    assert _from_proto.token_id == token_id
    assert _from_proto.serial_numbers == serial_numbers
    assert _from_proto.metadata == metadata_bytes
    
    # Test with empty protobuf
    empty_proto = TokenUpdateNftsTransactionBody()
    empty_tx = TokenUpdateNftsTransaction()._from_proto(empty_proto)
    
    # TokenId._from_proto with empty proto should return a new TokenId
    assert isinstance(empty_tx.token_id, TokenId)
    assert empty_tx.serial_numbers == []
    assert empty_tx.metadata is empty_proto.metadata.value  # Should be None or empty 