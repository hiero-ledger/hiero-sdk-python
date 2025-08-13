import pytest
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def custom_fees():
    """Fixture providing a list of custom fees for testing."""
    fixed_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )
    
    fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 789),
        all_collectors_are_exempt=True,
    )
    
    return [fixed_fee, fractional_fee]


def test_constructor_with_parameters(mock_account_ids, custom_fees):
    """Test creating a token fee schedule update transaction with constructor parameters."""
    _, _, _, token_id, _ = mock_account_ids
    
    tx = TokenFeeScheduleUpdateTransaction(
        token_id=token_id,
        custom_fees=custom_fees
    )
    
    assert tx.get_token_id() == token_id
    assert len(tx.get_custom_fees()) == 2
    assert isinstance(tx.get_custom_fees()[0], CustomFixedFee)
    assert isinstance(tx.get_custom_fees()[1], CustomFractionalFee)


def test_constructor_without_parameters():
    """Test creating a token fee schedule update transaction without parameters."""
    tx = TokenFeeScheduleUpdateTransaction()
    
    assert tx.get_token_id() is None
    assert len(tx.get_custom_fees()) == 0


def test_set_token_id(mock_account_ids):
    """Test setting the token ID."""
    _, _, _, token_id, _ = mock_account_ids
    
    tx = TokenFeeScheduleUpdateTransaction()
    result = tx.set_token_id(token_id)
    
    assert result is tx
    assert tx.get_token_id() == token_id


def test_set_custom_fees(custom_fees):
    """Test setting custom fees."""
    tx = TokenFeeScheduleUpdateTransaction()
    result = tx.set_custom_fees(custom_fees)
    
    assert result is tx
    assert len(tx.get_custom_fees()) == 2
    assert isinstance(tx.get_custom_fees()[0], CustomFixedFee)
    assert isinstance(tx.get_custom_fees()[1], CustomFractionalFee)


def test_set_custom_fees_empty():
    """Test setting empty custom fees list."""
    tx = TokenFeeScheduleUpdateTransaction()
    result = tx.set_custom_fees([])
    
    assert result is tx
    assert len(tx.get_custom_fees()) == 0


def test_set_custom_fees_none():
    """Test setting custom fees to None."""
    tx = TokenFeeScheduleUpdateTransaction()
    result = tx.set_custom_fees(None)
    
    assert result is tx
    assert len(tx.get_custom_fees()) == 0


def test_build_transaction_body(mock_account_ids, custom_fees):
    """Test building a token fee schedule update transaction body with valid values."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    
    tx = TokenFeeScheduleUpdateTransaction(
        token_id=token_id,
        custom_fees=custom_fees
    )
    
    tx.operator_account_id = operator_id
    tx.node_account_id = node_account_id
    transaction_body = tx.build_transaction_body()
    
    assert transaction_body.token_fee_schedule_update.token_id == token_id._to_proto()
    assert len(transaction_body.token_fee_schedule_update.custom_fees) == 2
    
    fees = transaction_body.token_fee_schedule_update.custom_fees
    
    assert fees[0].HasField("fixed_fee")
    assert fees[0].fixed_fee.amount == 100
    assert fees[0].all_collectors_are_exempt is False
    
    assert fees[1].HasField("fractional_fee")
    assert fees[1].fractional_fee.fractional_amount.numerator == 1
    assert fees[1].fractional_fee.fractional_amount.denominator == 10
    assert fees[1].all_collectors_are_exempt is True


def test_build_transaction_body_validation_errors():
    """Test that build_transaction_body raises appropriate validation errors."""
    tx = TokenFeeScheduleUpdateTransaction()
    
    tx.operator_account_id = AccountId(0, 0, 1)
    tx.node_account_id = AccountId(0, 0, 2)
    
    with pytest.raises(ValueError, match="Token ID is required"):
        tx.build_transaction_body()


def test_build_transaction_body_with_empty_fees(mock_account_ids):
    """Test building transaction body with empty custom fees list."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    
    tx = TokenFeeScheduleUpdateTransaction(
        token_id=token_id,
        custom_fees=[]
    )
    
    tx.operator_account_id = operator_id
    tx.node_account_id = node_account_id
    transaction_body = tx.build_transaction_body()
    
    assert transaction_body.token_fee_schedule_update.token_id == token_id._to_proto()
    assert len(transaction_body.token_fee_schedule_update.custom_fees) == 0


def test_token_fee_schedule_update_transaction_can_execute(mock_account_ids, custom_fees):
    """Test that a token fee schedule update transaction can be executed successfully."""
    _, _, _, token_id, _ = mock_account_ids

    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS
    )
    
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
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees(custom_fees)
            .freeze_with(client)
        )
        
        receipt = transaction.execute(client)
        assert receipt.status == ResponseCode.SUCCESS


def test_method_chaining(mock_account_ids, custom_fees):
    """Test method chaining for TokenFeeScheduleUpdateTransaction."""
    _, _, _, token_id, _ = mock_account_ids
    
    tx = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(custom_fees)
    )
    
    assert tx.get_token_id() == token_id
    assert len(tx.get_custom_fees()) == 2


def test_get_custom_fees_returns_copy():
    """Test that get_custom_fees returns a copy of the list."""
    fixed_fee = CustomFixedFee(amount=100)
    tx = TokenFeeScheduleUpdateTransaction(custom_fees=[fixed_fee])
    
    fees1 = tx.get_custom_fees()
    fees2 = tx.get_custom_fees()
    
    assert fees1 is not fees2
    assert len(fees1) == len(fees2) == 1
    assert fees1[0] is fees2[0]


def test_with_royalty_fee():
    """Test with a royalty fee in the custom fees list."""
    fallback_fee = CustomFixedFee(amount=50, denominating_token_id=TokenId(0, 0, 789))
    royalty_fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )
    
    tx = TokenFeeScheduleUpdateTransaction(custom_fees=[royalty_fee])
    
    assert len(tx.get_custom_fees()) == 1
    assert isinstance(tx.get_custom_fees()[0], CustomRoyaltyFee)