from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.token_fee_schedule_update_pb2 import TokenFeeScheduleUpdateTransactionBody
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)


pytestmark = pytest.mark.unit


def test_setters_and_constructor(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids
    collector_account = AccountId(0, 0, 987)
    test_fee_list = [CustomFixedFee(amount=100, fee_collector_account_id=collector_account)]

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
    test_fee_list = [CustomFixedFee(amount=200, fee_collector_account_id=collector_account)]

    txn = TokenFeeScheduleUpdateTransaction().set_token_id(token_id).set_custom_fees(test_fee_list)

    assert txn.token_id == token_id
    assert txn.custom_fees == test_fee_list
    assert len(txn.custom_fees) == 1


def test_build_proto_body_without_token_id_omits_field():
    """Missing token IDs omits field."""
    update_tx = TokenFeeScheduleUpdateTransaction().set_custom_fees(
        [
            CustomFixedFee(
                amount=100,
                fee_collector_account_id=AccountId(0, 0, 987),
            )
        ]
    )

    body = update_tx._build_proto_body()

    assert not body.HasField("token_id")
    assert len(body.custom_fees) == 1


def test_build_scheduled_body_without_token_id_omits_field():
    """Scheduled bodies should also omit missing token ID."""
    update_tx = TokenFeeScheduleUpdateTransaction().set_custom_fees(
        [CustomFixedFee(amount=50, fee_collector_account_id=AccountId(0, 0, 123))]
    )

    scheduled_body = update_tx.build_scheduled_body()

    assert scheduled_body.HasField("token_fee_schedule_update")
    assert not scheduled_body.token_fee_schedule_update.HasField("token_id")
    assert len(scheduled_body.token_fee_schedule_update.custom_fees) == 1


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
    test_fee = CustomFixedFee(amount=150, fee_collector_account_id=operator_id)
    test_fees_list = [test_fee]

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


def test_from_protobuf(mock_account_ids):
    """Test deserialization of TokenFeeScheduleUpdateTransaction from protobuf with all fields populated."""
    account_id_1, account_id_2, _, token_id, _ = mock_account_ids
    custom_fees = [
        CustomFixedFee(amount=15, fee_collector_account_id=account_id_1),
        CustomFixedFee(amount=10, fee_collector_account_id=account_id_2),
    ]

    proto = TokenFeeScheduleUpdateTransactionBody(
        token_id=token_id._to_proto(), custom_fees=[custom_fee._to_proto() for custom_fee in custom_fees]
    )
    tx = TokenFeeScheduleUpdateTransaction._from_protobuf(TransactionBody(token_fee_schedule_update=proto))

    assert tx is not None
    assert isinstance(tx, TokenFeeScheduleUpdateTransaction)
    assert tx.token_id == token_id
    assert len(tx.custom_fees) == len(custom_fees)
    for indx, fee in enumerate(custom_fees):
        assert tx.custom_fees[indx] == fee


def test_from_protobuf_with_defaults():
    """Test deserialization of TokenFeeScheduleUpdateTransaction from protobuf with default field values."""
    proto = TokenFeeScheduleUpdateTransactionBody()
    tx = TokenFeeScheduleUpdateTransaction._from_protobuf(TransactionBody(token_fee_schedule_update=proto))

    assert tx is not None
    assert isinstance(tx, TokenFeeScheduleUpdateTransaction)
    assert tx.token_id is None
    assert tx.custom_fees == []


def test_from_protobuf_without_token_fee_schedule_update():
    """Test deserialization of TokenFeeScheduleUpdateTransaction from a TransactionBody without a token update."""
    tx = TokenFeeScheduleUpdateTransaction._from_protobuf(TransactionBody())

    assert tx is not None
    assert isinstance(tx, TokenFeeScheduleUpdateTransaction)
    assert tx.token_id is None
    assert tx.custom_fees == []


def test_bytes_roundtrip(mock_account_ids):
    """Test serialization and deserialization of TokenFeeScheduleUpdateTransaction through bytes."""
    account_id_1, account_id_2, _, token_id, _ = mock_account_ids
    custom_fees = [
        CustomFixedFee(amount=15, fee_collector_account_id=account_id_1),
        CustomFixedFee(amount=10, fee_collector_account_id=account_id_2),
    ]

    original_tx = TokenFeeScheduleUpdateTransaction(token_id=token_id, custom_fees=custom_fees)
    original_bytes = original_tx.to_bytes()

    copy_tx = TokenFeeScheduleUpdateTransaction.from_bytes(original_bytes)

    assert copy_tx is not None
    assert copy_tx.to_bytes() == original_bytes
    assert isinstance(copy_tx, TokenFeeScheduleUpdateTransaction)
    assert copy_tx.token_id == token_id
    assert len(copy_tx.custom_fees) == len(custom_fees)
    for indx, fee in enumerate(custom_fees):
        assert copy_tx.custom_fees[indx] == fee
