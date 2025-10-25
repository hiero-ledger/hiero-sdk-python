import pytest
from unittest.mock import MagicMock

from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import SchedulableTransactionBody

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_account_ids():
    operator_id = AccountId(0, 0, 123)
    node_account_id = AccountId(0, 0, 3)
    token_id = TokenId(0, 0, 456)
    return operator_id, None, node_account_id, token_id, None

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.freeze_with = MagicMock(return_value=None)
    return client

def test_setters_and_constructor(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids
    collector_account = AccountId(0, 0, 987)
    test_fee_list = [CustomFixedFee(amount=100, fee_collector_account_id=collector_account)]
    txn = TokenFeeScheduleUpdateTransaction()
    txn.set_token_id(token_id)
    txn.set_custom_fees(test_fee_list)
    assert txn._token_id == token_id
    assert txn._custom_fees == test_fee_list
    assert len(txn._custom_fees) == 1

def test_build_raises_error_if_no_token_id():
    update_tx = TokenFeeScheduleUpdateTransaction()
    test_fee_list = [CustomFixedFee(amount=100, fee_collector_account_id=AccountId(0, 0, 987))]
    update_tx.set_custom_fees(test_fee_list)
    with pytest.raises(ValueError, match="Missing token ID"):
        update_tx.build_transaction_body()

def test_build_transaction_body_correctly(mock_account_ids):
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    test_fee_fixed = CustomFixedFee(amount=150, fee_collector_account_id=operator_id)
    test_fee_royalty = CustomRoyaltyFee(numerator=5, denominator=10, fee_collector_account_id=operator_id)
    test_fees_list = [test_fee_fixed, test_fee_royalty]
    update_tx = TokenFeeScheduleUpdateTransaction()
    update_tx.set_token_id(token_id)
    update_tx.set_custom_fees(test_fees_list)
    update_tx.operator_account_id = operator_id
    update_tx.node_account_id = node_account_id
    transaction_body = update_tx.build_transaction_body()

    assert transaction_body.HasField("tokenFeeScheduleUpdate")
    assert transaction_body.tokenFeeScheduleUpdate.tokenId == token_id._to_proto()
    assert len(transaction_body.tokenFeeScheduleUpdate.customFees) == 2

    proto_fee_fixed = transaction_body.tokenFeeScheduleUpdate.customFees[0]
    assert proto_fee_fixed.fixed_fee.amount == 150
    assert proto_fee_fixed.fee_collector_account_id == operator_id._to_proto()

    proto_fee_royalty = transaction_body.tokenFeeScheduleUpdate.customFees[1]
    assert proto_fee_royalty.royalty_fee.numerator == 5
    assert proto_fee_royalty.royalty_fee.denominator == 10
    assert proto_fee_royalty.fee_collector_account_id == operator_id._to_proto()

def test_build_scheduled_body(mock_account_ids):
    operator_id, _, _, token_id, _ = mock_account_ids
    test_fee = CustomFixedFee(amount=100, fee_collector_account_id=operator_id)
    update_tx = TokenFeeScheduleUpdateTransaction().set_token_id(token_id).set_custom_fees([test_fee])
    schedulable_body = update_tx.build_scheduled_body()
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenFeeScheduleUpdate")
    assert schedulable_body.tokenFeeScheduleUpdate.tokenId == token_id._to_proto()
    assert len(schedulable_body.tokenFeeScheduleUpdate.customFees) == 1
    assert schedulable_body.tokenFeeScheduleUpdate.customFees[0].fixed_fee.amount == 100

def test_set_methods_require_not_frozen(mock_account_ids, mock_client):
    _, _, _, token_id, _ = mock_account_ids
    test_fee = CustomFixedFee(amount=100, fee_collector_account_id=AccountId(0, 0, 987))
    update_tx = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=[])
    update_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        update_tx.set_token_id(token_id)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        update_tx.set_custom_fees([test_fee])
