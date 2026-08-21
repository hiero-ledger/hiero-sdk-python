from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)


pytestmark = pytest.mark.unit


def test_setters_and_constructor(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids
    collector_account = AccountId(0, 0, 987)
    test_fee_list: list[CustomFee] = [CustomFixedFee(amount=100, fee_collector_account_id=collector_account)]

    txn_constructor = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=test_fee_list)
    assert txn_constructor.token_id == token_id
    assert txn_constructor.custom_fees == test_fee_list

    txn_setters = TokenFeeScheduleUpdateTransaction()
    txn_setters.set_token_id(token_id)
    txn_setters.set_custom_fees(test_fee_list)

    assert txn_setters.token_id == token_id
    assert txn_setters.custom_fees == test_fee_list
    assert len(txn_setters.custom_fees) == 1


def test_setters_chaining(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids
    collector_account = AccountId(0, 0, 987)
    test_fee_list: list[CustomFee] = [CustomFixedFee(amount=200, fee_collector_account_id=collector_account)]

    txn = TokenFeeScheduleUpdateTransaction().set_token_id(token_id).set_custom_fees(test_fee_list)

    assert txn.token_id == token_id
    assert txn.custom_fees == test_fee_list
    assert len(txn.custom_fees) == 1


def test_build_allows_missing_token_id(mock_account_ids):
    operator_id, _, node_account_id, _, _ = mock_account_ids
    update_tx = TokenFeeScheduleUpdateTransaction()
    test_fee_list: list[CustomFee] = [CustomFixedFee(amount=100, fee_collector_account_id=AccountId(0, 0, 987))]
    update_tx.operator_account_id = operator_id
    update_tx.set_node_account_ids([node_account_id])
    update_tx.set_custom_fees(test_fee_list)

    transaction_body = update_tx.build_transaction_body()

    assert transaction_body.HasField("token_fee_schedule_update")
    assert not transaction_body.token_fee_schedule_update.HasField("token_id")


def test_build_without_token_id_omits_field(mock_account_ids):
    """Token ID should be omitted so the network can reject it."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    new_fee: CustomFee = CustomFixedFee(amount=50, fee_collector_account_id=AccountId(0, 0, 123))
    update_tx = TokenFeeScheduleUpdateTransaction().set_custom_fees([new_fee])
    update_tx.operator_account_id = operator_id
    update_tx.set_node_account_ids([node_account_id])

    transaction_body = update_tx.build_transaction_body()

    assert transaction_body.HasField("token_fee_schedule_update")
    assert not transaction_body.token_fee_schedule_update.HasField("token_id")


def test_build_transaction_body_sets_token_id(mock_account_ids):
    operator_id, _, node_account_id, token_id, _ = mock_account_ids

    update_tx = TokenFeeScheduleUpdateTransaction(token_id=token_id)
    update_tx.operator_account_id = operator_id
    update_tx.set_node_account_ids([node_account_id])

    transaction_body = update_tx.build_transaction_body()

    assert transaction_body.HasField("token_fee_schedule_update")
    assert transaction_body.token_fee_schedule_update.token_id == token_id._to_proto()


def test_build_transaction_body_sets_custom_fees(mock_account_ids):
    operator_id, _, node_account_id, token_id, _ = mock_account_ids
    test_fee: CustomFee = CustomFixedFee(amount=150, fee_collector_account_id=operator_id)
    test_fees_list: list[CustomFee] = [test_fee]

    update_tx = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=test_fees_list)
    update_tx.operator_account_id = operator_id
    update_tx.set_node_account_ids([node_account_id])

    transaction_body = update_tx.build_transaction_body()

    assert len(transaction_body.token_fee_schedule_update.custom_fees) == 1
    proto_fee = transaction_body.token_fee_schedule_update.custom_fees[0]
    assert proto_fee.fixed_fee.amount == 150
    assert proto_fee.fee_collector_account_id == operator_id._to_proto()


def test_build_transaction_body_with_empty_custom_fees(mock_account_ids):
    """Test for empty custom fee list."""
    operator_id, _, node_account_id, token_id, _ = mock_account_ids

    update_tx = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=[])
    update_tx.operator_account_id = operator_id
    update_tx.set_node_account_ids([node_account_id])

    transaction_body = update_tx.build_transaction_body()

    assert transaction_body.HasField("token_fee_schedule_update")
    assert transaction_body.token_fee_schedule_update.token_id == token_id._to_proto()
    assert len(transaction_body.token_fee_schedule_update.custom_fees) == 0


def test_get_method_returns_token_service_method():
    channel = _Channel()
    token_service = MagicMock()
    channel._token = token_service

    method = TokenFeeScheduleUpdateTransaction()._get_method(channel)

    assert method.transaction == token_service.updateTokenFeeSchedule


def test_get_method_raises_when_token_service_unavailable():
    channel = _Channel()

    with pytest.raises(ValueError, match="Token service not available on channel"):
        TokenFeeScheduleUpdateTransaction()._get_method(channel)


def test_repr_includes_token_id_and_fee_count(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids
    transaction = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=[])

    representation = repr(transaction)

    assert "TokenFeeScheduleUpdateTransaction" in representation
    assert "fees=0" in representation
