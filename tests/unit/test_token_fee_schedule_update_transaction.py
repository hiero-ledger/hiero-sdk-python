import pytest

from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
# This is the key import from token_create_transaction.py
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee

pytestmark = pytest.mark.unit

def test_setters_and_constructor(mock_account_ids):
    """
    Test Case 1: Check the setters and constructor.
    (Pattern from test_token_update_transaction.py: test_set_methods)
    """
    # 1. Get test "ingredients"
    _, _, _, token_id, _ = mock_account_ids
    collector_account = AccountId(0, 0, 987)

    # 2. Create your new test data
    test_fee_list = [
        CustomFixedFee(amount=100, fee_collector_account_id=collector_account)
    ]

    # 3. Create class and use setters
    txn = TokenFeeScheduleUpdateTransaction()
    txn.set_token_id(token_id)
    txn.set_custom_fees(test_fee_list)

    # 4. Check that the class stored the values
    assert txn._token_id == token_id
    assert txn._custom_fees == test_fee_list
    assert len(txn._custom_fees) == 1


def test_build_raises_error_if_no_token_id():
    """
    Test Case 2: Check the error handling.
    (Pattern from test_token_update_transaction.py: test_build_transaction_body_validation_errors)
    """
    # 1. Create a transaction *without* a token ID
    update_tx = TokenFeeScheduleUpdateTransaction()
    
    # 2. Set some fees
    test_fee_list = [
        CustomFixedFee(amount=100, fee_collector_account_id=AccountId(0, 0, 987))
    ]
    update_tx.set_custom_fees(test_fee_list)

    # 3. Check that it raises the correct error when we try to build
    with pytest.raises(ValueError, match="Missing token ID"):
        # We call build_transaction_body(), which in turn calls _build_proto_body()
        update_tx.build_transaction_body()


def test_build_transaction_body_correctly(mock_account_ids):
    """
    Test Case 3: Check the final protobuf object.
    (Pattern from test_token_update_transaction.py: test_build_transaction_body)
    """
    
    # 1. Get test "ingredients"
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    
    # 2. Create your test fees
    test_fee = CustomFixedFee(
        amount=150, 
        fee_collector_account_id=operator_id
    )
    test_fees_list = [test_fee]

    # 3. Create your class
    update_tx = TokenFeeScheduleUpdateTransaction()
    update_tx.set_token_id(token_id)
    update_tx.set_custom_fees(test_fees_list)

    # 4. Set required operator and node IDs (THIS IS A CRITICAL STEP)
    update_tx.operator_account_id = operator_id
    update_tx.node_account_id = node_account_id
    
    # 5. Build the final transaction body
    transaction_body = update_tx.build_transaction_body()
    
    # 6. Check the protobuf fields to make sure they are correct
    
    # Check that the correct transaction type was used
    assert transaction_body.HasField("token_fee_schedule_update")
    
    # Check the token ID
    assert transaction_body.token_fee_schedule_update.token_id == token_id._to_proto()
    
    # Check that the custom fees list was built and has 1 item
    assert len(transaction_body.token_fee_schedule_update.custom_fees) == 1

    # Check the details of the fee itself
    proto_fee = transaction_body.token_fee_schedule_update.custom_fees[0]
    assert proto_fee.fixed_fee.amount == 150
    assert proto_fee.fee_collector_account_id == operator_id._to_proto()
