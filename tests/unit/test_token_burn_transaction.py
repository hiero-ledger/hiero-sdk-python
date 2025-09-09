import pytest

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.token_burn_pb2 import TokenBurnTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token burn transaction with constructor parameters."""
    _, _, _, token_id, _ = mock_account_ids

    burn_tx = TokenBurnTransaction(
        token_id=token_id,
        amount=100
    )

    assert burn_tx.token_id == token_id
    assert burn_tx.amount == 100
    assert burn_tx.serials == []
    
    burn_tx = TokenBurnTransaction(
        token_id=token_id,
        serials=[1, 2, 3]
    )
    
    assert burn_tx.token_id == token_id
    assert burn_tx.serials == [1, 2, 3]

def test_build_transaction_body(mock_account_ids):
    """Test building a token burn transaction body with valid values."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids

    burn_tx = TokenBurnTransaction(token_id=token_id, amount=100)

    # Set operator and node account IDs needed for building transaction body
    burn_tx.operator_account_id = operator_id
    burn_tx.node_account_id = node_account_id
    transaction_body = burn_tx.build_transaction_body()

    assert transaction_body.tokenBurn.token == token_id._to_proto()
    assert transaction_body.tokenBurn.amount == 100

def test_build_transaction_body_validation_errors():
    """Test that build_transaction_body raises appropriate validation errors."""
    burn_tx = TokenBurnTransaction()

    with pytest.raises(ValueError, match="Missing token ID"):
        burn_tx.build_transaction_body()
    
    with pytest.raises(ValueError, match="Cannot burn both amount and serial in the same transaction"):
        burn_tx.set_token_id(TokenId(0, 0, 0)).set_amount(100).set_serials([1, 2, 3]).build_transaction_body()

def test_set_methods(mock_account_ids):
    """Test the set methods of TokenBurnTransaction."""
    _, _, _, token_id, _ = mock_account_ids

    burn_tx = TokenBurnTransaction()

    test_cases = [
        ('set_token_id', token_id, 'token_id'),
        ('set_amount', 100, 'amount'),
        ('set_serials', [1, 2, 3], 'serials')
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(burn_tx, method_name)(value)
        assert tx_after_set is burn_tx
        assert getattr(burn_tx, attr_name) == value

def test_set_methods_require_not_frozen(mock_account_ids, mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    _, _, _, token_id, _ = mock_account_ids

    burn_tx = TokenBurnTransaction(token_id=token_id, amount=100)
    burn_tx.freeze_with(mock_client)

    test_cases = [
        ('set_token_id', token_id),
        ('set_amount', 200),
        ('set_serials', [1, 2, 3])
    ]

    for method_name, value in test_cases:
        with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
            getattr(burn_tx, method_name)(value)

def test_burn_transaction_can_execute(mock_account_ids):
    """Test that a token burn transaction can be executed successfully."""
    _, _, _, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token burn
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
            TokenBurnTransaction()
            .set_token_id(token_id)
            .set_amount(100)
        )

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"
        
def test_burn_transaction_from_proto(mock_account_ids):
    """Test that a burn transaction can be created from a protobuf object."""
    _, _, _, token_id, _ = mock_account_ids

    # Create protobuf object with token burn details
    proto = TokenBurnTransactionBody(
        token=token_id._to_proto(),
        amount=100,
        serialNumbers=[1, 2, 3]
    )
    
    # Deserialize the protobuf object
    from_proto = TokenBurnTransaction()._from_proto(proto)
    
    # Verify deserialized transaction matches original data
    assert from_proto.token_id == token_id
    assert from_proto.amount == 100
    assert from_proto.serials == [1, 2, 3]
    
    # Deserialize empty protobuf
    from_proto = TokenBurnTransaction()._from_proto(TokenBurnTransactionBody())
    
    # Verify empty protobuf deserializes to empty/default values
    assert from_proto.token_id == TokenId(0,0,0)
    assert from_proto.amount == 0
    assert from_proto.serials == []
    
def test_build_scheduled_body_fungible(mock_account_ids):
    """Test building a scheduled transaction body for fungible token burn transaction."""
    _, _, _, token_id, _ = mock_account_ids
    
    burn_tx = TokenBurnTransaction()
    burn_tx.set_token_id(token_id)
    burn_tx.set_amount(100)
    
    schedulable_body = burn_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenBurn")
    assert schedulable_body.tokenBurn.token == token_id._to_proto()
    assert schedulable_body.tokenBurn.amount == 100
    assert len(schedulable_body.tokenBurn.serialNumbers) == 0
    
def test_build_scheduled_body_nft(mock_account_ids):
    """Test building a scheduled transaction body for NFT burn transaction."""
    _, _, _, token_id, _ = mock_account_ids
    serials = [1, 2, 3]
    
    burn_tx = TokenBurnTransaction()
    burn_tx.set_token_id(token_id)
    burn_tx.set_serials(serials)
    
    schedulable_body = burn_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenBurn")
    assert schedulable_body.tokenBurn.token == token_id._to_proto()
    assert schedulable_body.tokenBurn.amount == 0
    assert schedulable_body.tokenBurn.serialNumbers == serials