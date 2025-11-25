import pytest

from hiero_sdk_python.hapi.services.token_grant_kyc_pb2 import TokenGrantKycTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_build_transaction_body(mock_account_ids):
    """Test building a token grant KYC transaction body with valid values."""
    account_id, _, node_account_id, token_id, _ = mock_account_ids

    grant_kyc_tx = (
        TokenGrantKycTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
    )
    
    # Set operator and node account IDs needed for building transaction body
    grant_kyc_tx.operator_account_id = account_id
    grant_kyc_tx.node_account_id = node_account_id
    
    transaction_body = grant_kyc_tx.build_transaction_body()

    assert transaction_body.tokenGrantKyc.token == token_id._to_proto()
    assert transaction_body.tokenGrantKyc.account == account_id._to_proto()

def test_build_transaction_body_validation(mock_account_ids):
    """Test validation when building transaction body."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Test missing token ID
    grant_kyc_tx = TokenGrantKycTransaction(account_id=account_id)
    
    with pytest.raises(ValueError, match="Missing token ID"):
        grant_kyc_tx.build_transaction_body()

    # Test missing account ID
    grant_kyc_tx = TokenGrantKycTransaction(token_id=token_id)
    
    with pytest.raises(ValueError, match="Missing account ID"):
        grant_kyc_tx.build_transaction_body()


def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token grant KYC transaction with constructor parameters."""
    account_id, _, _, token_id, _ = mock_account_ids

    grant_kyc_tx = TokenGrantKycTransaction(
        token_id=token_id,
        account_id=account_id
    )

    assert grant_kyc_tx.token_id == token_id
    assert grant_kyc_tx.account_id == account_id

def test_set_methods(mock_account_ids):
    """Test the set methods of TokenGrantKycTransaction."""
    account_id, _, _, token_id, _ = mock_account_ids

    grant_kyc_tx = TokenGrantKycTransaction()
    
    # Test method chaining
    tx_after_set = grant_kyc_tx.set_token_id(token_id)
    assert tx_after_set is grant_kyc_tx
    assert grant_kyc_tx.token_id == token_id
    
    tx_after_set = grant_kyc_tx.set_account_id(account_id)
    assert tx_after_set is grant_kyc_tx
    assert grant_kyc_tx.account_id == account_id

def test_set_methods_require_not_frozen(mock_account_ids, mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    account_id, _, _, token_id, _ = mock_account_ids

    grant_kyc_tx = TokenGrantKycTransaction(token_id=token_id, account_id=account_id)
    grant_kyc_tx.freeze_with(mock_client)
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        grant_kyc_tx.set_token_id(token_id)
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        grant_kyc_tx.set_account_id(account_id)

def test_grant_kyc_transaction_can_execute(mock_account_ids):
    """Test that a grant KYC transaction can be executed successfully."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful token grant KYC
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
            TokenGrantKycTransaction()
            .set_token_id(token_id)
            .set_account_id(account_id)
        )
        
        receipt = transaction.execute(client)
        
        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"

def test_grant_kyc_transaction_from_proto(mock_account_ids):
    """Test that a grant KYC transaction can be created from a protobuf object."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Create protobuf object
    proto = TokenGrantKycTransactionBody(
        token=token_id._to_proto(),
        account=account_id._to_proto()
    )
    
    # Deserialize the protobuf object
    from_proto = TokenGrantKycTransaction()._from_proto(proto)
    
    # Verify deserialized transaction matches original data
    assert from_proto.token_id == token_id
    assert from_proto.account_id == account_id
    
    # Deserialize empty protobuf
    from_proto = TokenGrantKycTransaction()._from_proto(TokenGrantKycTransactionBody())
    
    # Verify empty protobuf deserializes to empty/default values
    assert from_proto.token_id == TokenId(0,0,0)
    assert from_proto.account_id == AccountId()
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token grant KYC transaction."""
    account_id, _, _, token_id, _ = mock_account_ids
    
    grant_kyc_tx = TokenGrantKycTransaction()
    grant_kyc_tx.set_token_id(token_id)
    grant_kyc_tx.set_account_id(account_id)

    schedulable_body = grant_kyc_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenGrantKyc")
    assert schedulable_body.tokenGrantKyc.token == token_id._to_proto()
    assert schedulable_body.tokenGrantKyc.account == account_id._to_proto()