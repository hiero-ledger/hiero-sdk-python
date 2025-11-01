import datetime
import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKeyValidation
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateKeys, TokenUpdateParams, TokenUpdateTransaction
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

@pytest.fixture
def new_token_data():
    return {
        "name": "Test Token",
        "symbol": "TTK",
        "memo": "Test memo",
        "metadata": b"Test metadata",
        "auto_renew_period": Duration(7776000),
        "expiration_time": Timestamp.from_date(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        )
    }

def test_constructor_with_parameters(mock_account_ids, private_key, new_token_data):
    """Test creating a token update transaction with constructor parameters."""
    operator_id, _, _, token_id, _ = mock_account_ids

    token_params = TokenUpdateParams(
        token_name=new_token_data["name"],
        token_symbol=new_token_data["symbol"],
        token_memo=new_token_data["memo"],
        metadata=new_token_data["metadata"],
        treasury_account_id=operator_id,
        auto_renew_account_id=operator_id,
        auto_renew_period=new_token_data["auto_renew_period"],
        expiration_time=new_token_data["expiration_time"]
    )
    
    token_keys = TokenUpdateKeys(
        admin_key=private_key,
        metadata_key=private_key,
    )

    update_tx = TokenUpdateTransaction(
        token_id=token_id,
        token_params=token_params,
        token_keys=token_keys,
        token_key_verification_mode=TokenKeyValidation.FULL_VALIDATION
    )

    assert update_tx.token_id == token_id
    assert update_tx.token_name == new_token_data["name"]
    assert update_tx.token_symbol == new_token_data["symbol"]
    assert update_tx.token_memo == new_token_data["memo"]    
    assert update_tx.metadata == new_token_data["metadata"]
    assert update_tx.admin_key == private_key
    assert update_tx.metadata_key == private_key
    assert update_tx.treasury_account_id == operator_id
    assert update_tx.auto_renew_account_id == operator_id
    assert update_tx.auto_renew_period == new_token_data["auto_renew_period"]
    assert update_tx.expiration_time == new_token_data["expiration_time"]
    assert update_tx.token_key_verification_mode == TokenKeyValidation.FULL_VALIDATION
    assert update_tx.freeze_key is None
    assert update_tx.wipe_key is None
    assert update_tx.supply_key is None
    assert update_tx.pause_key is None
    assert update_tx.kyc_key is None
    assert update_tx.fee_schedule_key is None

def test_build_transaction_body(mock_account_ids, new_token_data):
    """Test building a token update transaction body with valid values."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids

    token_update_params = TokenUpdateParams(
        treasury_account_id=operator_id, 
        token_name=new_token_data["name"], 
        token_symbol=new_token_data["symbol"], 
        token_memo=new_token_data["memo"],
        metadata=new_token_data["metadata"],
        auto_renew_account_id=operator_id,
        auto_renew_period=new_token_data["auto_renew_period"],
        expiration_time=new_token_data["expiration_time"]
    )
    
    update_tx = TokenUpdateTransaction(token_id=token_id, token_params=token_update_params)
    
    # Set operator and node account IDs needed for building transaction body
    update_tx.operator_account_id = operator_id
    update_tx.node_account_id = node_account_id
    transaction_body = update_tx.build_transaction_body()
    
    assert transaction_body.tokenUpdate.token == token_id._to_proto()
    assert transaction_body.tokenUpdate.treasury == operator_id._to_proto()
    assert transaction_body.tokenUpdate.name == new_token_data["name"]
    assert transaction_body.tokenUpdate.symbol == new_token_data["symbol"]
    assert transaction_body.tokenUpdate.memo.value == new_token_data["memo"]
    assert transaction_body.tokenUpdate.metadata.value == new_token_data["metadata"]
    assert transaction_body.tokenUpdate.autoRenewPeriod == new_token_data["auto_renew_period"]._to_proto()
    assert transaction_body.tokenUpdate.autoRenewAccount == operator_id._to_proto()
    assert transaction_body.tokenUpdate.expiry.seconds == new_token_data["expiration_time"].seconds
    assert transaction_body.tokenUpdate.key_verification_mode == TokenKeyValidation.FULL_VALIDATION

def test_build_transaction_body_validation_errors():
    """Test that build_transaction_body raises appropriate validation errors."""
    # Test missing token_id
    update_tx = TokenUpdateTransaction()
    
    with pytest.raises(ValueError, match="Missing token ID"):
        update_tx.build_transaction_body()

def test_set_methods(mock_account_ids, private_key, new_token_data):
    """Test the set methods of TokenUpdateTransaction."""
    operator_id, _, _, token_id, _ = mock_account_ids
    
    update_tx = TokenUpdateTransaction(token_id=token_id)
    
    test_cases = [
        ('set_token_id', token_id, 'token_id'),
        ('set_token_name', new_token_data["name"], 'token_name'),
        ('set_token_symbol', new_token_data["symbol"], 'token_symbol'), 
        ('set_token_memo', new_token_data["memo"], 'token_memo'),
        ('set_metadata', new_token_data["metadata"], 'metadata'),
        ('set_expiration_time', new_token_data["expiration_time"], 'expiration_time'),
        ('set_auto_renew_period', new_token_data["auto_renew_period"], 'auto_renew_period'),
        ('set_auto_renew_account_id', operator_id, 'auto_renew_account_id'),
        ('set_admin_key', private_key, 'admin_key'),
        ('set_freeze_key', private_key, 'freeze_key'),
        ('set_wipe_key', private_key, 'wipe_key'),
        ('set_supply_key', private_key, 'supply_key'),
        ('set_metadata_key', private_key, 'metadata_key'),
        ('set_pause_key', private_key, 'pause_key'),
        ('set_kyc_key', private_key, 'kyc_key'),
        ('set_fee_schedule_key', private_key, 'fee_schedule_key')
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(update_tx, method_name)(value)
        assert tx_after_set is update_tx
        assert getattr(update_tx, attr_name) == value

def test_set_methods_require_not_frozen(mock_account_ids, mock_client, new_token_data):
    """Test that set methods raise exception when transaction is frozen."""
    operator_id, _, _, token_id, _ = mock_account_ids

    update_tx = TokenUpdateTransaction(
        token_id=token_id,
        token_params=TokenUpdateParams(token_name=new_token_data["name"])
    )
    update_tx.freeze_with(mock_client)
    
    private_key = mock_client.operator_private_key
    
    test_cases = [
        ('set_token_id', token_id),
        ('set_token_name', new_token_data["name"]),
        ('set_token_symbol', new_token_data["symbol"]), 
        ('set_token_memo', new_token_data["memo"]),
        ('set_metadata', new_token_data["metadata"]),
        ('set_expiration_time', new_token_data["expiration_time"]),
        ('set_auto_renew_period', new_token_data["auto_renew_period"]),
        ('set_auto_renew_account_id', operator_id),
        ('set_admin_key', private_key),
        ('set_freeze_key', private_key),
        ('set_wipe_key', private_key),
        ('set_supply_key', private_key),
        ('set_metadata_key', private_key),
        ('set_pause_key', private_key),
        ('set_kyc_key', private_key),
        ('set_fee_schedule_key', private_key)
    ]
    
    # Test all set methods raise exception when frozen
    for method_name, value in test_cases:
        with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
            getattr(update_tx, method_name)(value)
        

def test_update_transaction_can_execute(mock_account_ids, new_token_data):
    """Test that a token update transaction can be executed successfully."""
    _, _, _, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful token update
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
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name(new_token_data["name"])
            .set_token_symbol(new_token_data["symbol"])
            .set_token_memo(new_token_data["memo"])
            .set_metadata(new_token_data["metadata"])
        )
        
        receipt = transaction.execute(client)
        
        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"

def test_build_scheduled_body(mock_account_ids, private_key, new_token_data):
    """Test building a scheduled transaction body for token update transaction."""
    operator_id, _, _, token_id, _ = mock_account_ids
    
    update_tx = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_token_name(new_token_data["name"])
        .set_token_symbol(new_token_data["symbol"])
        .set_token_memo(new_token_data["memo"])
        .set_metadata(new_token_data["metadata"])
        .set_expiration_time(new_token_data["expiration_time"])
        .set_auto_renew_period(new_token_data["auto_renew_period"])
        .set_auto_renew_account_id(operator_id)
        .set_treasury_account_id(operator_id)
        .set_admin_key(private_key)
    )
    schedulable_body = update_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenUpdate")
    assert schedulable_body.tokenUpdate.token == token_id._to_proto()
    assert schedulable_body.tokenUpdate.name == new_token_data["name"]
    assert schedulable_body.tokenUpdate.symbol == new_token_data["symbol"]
    assert schedulable_body.tokenUpdate.memo.value == new_token_data["memo"]
    assert schedulable_body.tokenUpdate.metadata.value == new_token_data["metadata"]
    assert schedulable_body.tokenUpdate.expiry.seconds == new_token_data["expiration_time"].seconds
    assert schedulable_body.tokenUpdate.autoRenewPeriod == new_token_data["auto_renew_period"]._to_proto()
    assert schedulable_body.tokenUpdate.autoRenewAccount == operator_id._to_proto()
    assert schedulable_body.tokenUpdate.treasury == operator_id._to_proto()
    assert schedulable_body.tokenUpdate.adminKey.HasField("ed25519")
