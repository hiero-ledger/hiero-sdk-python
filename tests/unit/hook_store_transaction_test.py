"""Unit tests for HookStoreTransaction."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.hooks.evm_hook_mapping_entry import EvmHookMappingEntry
from hiero_sdk_python.hooks.evm_hook_storage_update import EvmHookMappingEntries, EvmHookStorageSlot
from hiero_sdk_python.hooks.hook_entity_id import HookEntityId
from hiero_sdk_python.hooks.hook_id import HookId
from hiero_sdk_python.hooks.hook_store_transaction import HookStoreTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


@pytest.fixture
def hook_id():
    """A hook owned by account 0.0.5."""
    return HookId(HookEntityId(account_id=AccountId(0, 0, 5)), 1)


@pytest.fixture
def storage_updates():
    """One slot write and one mapping write."""
    return [
        EvmHookStorageSlot(key=b"\x01", value=b"\x02"),
        EvmHookMappingEntries(mapping_slot=b"\x03", entries=[EvmHookMappingEntry.with_key(b"\x04", b"\x05")]),
    ]


def test_constructor_sets_fields(hook_id, storage_updates):
    tx = HookStoreTransaction(hook_id=hook_id, storage_updates=storage_updates)

    assert tx.hook_id == hook_id
    assert tx.storage_updates == storage_updates
    assert tx.storage_updates is not storage_updates


def test_constructor_defaults():
    tx = HookStoreTransaction()

    assert tx.hook_id is None
    assert tx.storage_updates == []


def test_setters_chain(hook_id, storage_updates):
    tx = HookStoreTransaction()

    result = tx.set_hook_id(hook_id).set_storage_updates(storage_updates[:1]).add_storage_update(storage_updates[1])

    assert result is tx
    assert tx.storage_updates == storage_updates


def test_setters_reject_wrong_types(hook_id):
    tx = HookStoreTransaction()

    with pytest.raises(TypeError):
        tx.set_hook_id(AccountId(0, 0, 5))
    with pytest.raises(TypeError):
        tx.set_storage_updates([b"\x01"])
    with pytest.raises(TypeError):
        tx.set_storage_updates(EvmHookStorageSlot())
    with pytest.raises(TypeError):
        tx.add_storage_update(b"\x01")


def test_build_transaction_body(mock_account_ids, hook_id, storage_updates):
    operator_id, _, node_account_id, _, _ = mock_account_ids
    tx = HookStoreTransaction(hook_id=hook_id, storage_updates=storage_updates)
    tx.operator_account_id = operator_id
    tx.set_node_account_ids([node_account_id])

    body = tx.build_transaction_body()

    assert body.WhichOneof("data") == "hook_store"
    assert body.hook_store.hook_id == hook_id._to_proto()
    assert [update.WhichOneof("update") for update in body.hook_store.storage_updates] == [
        "storage_slot",
        "mapping_entries",
    ]


def test_build_contract_owned_hook(mock_account_ids):
    operator_id, _, node_account_id, _, _ = mock_account_ids
    hook_id = HookId(HookEntityId(contract_id=ContractId(0, 0, 9)), 2)
    tx = HookStoreTransaction(hook_id=hook_id)
    tx.operator_account_id = operator_id
    tx.set_node_account_ids([node_account_id])

    body = tx.build_transaction_body()

    assert body.hook_store.hook_id.entity_id.contract_id.contractNum == 9
    assert len(body.hook_store.storage_updates) == 0


def test_build_requires_hook_id():
    with pytest.raises(ValueError, match="Missing required HookId"):
        HookStoreTransaction().build_transaction_body()


def test_cannot_be_scheduled(hook_id):
    with pytest.raises(ValueError, match="Cannot schedule a HookStoreTransaction"):
        HookStoreTransaction(hook_id=hook_id).schedule()


def test_get_method():
    channel = MagicMock()

    method = HookStoreTransaction()._get_method(channel)

    assert method.query is None
    assert method.transaction == channel.smart_contract.hookStore


def test_frozen_transaction_is_immutable(mock_client, hook_id):
    tx = HookStoreTransaction(hook_id=hook_id).freeze_with(mock_client)

    with pytest.raises(Exception, match="frozen"):
        tx.set_hook_id(hook_id)
    with pytest.raises(Exception, match="frozen"):
        tx.add_storage_update(EvmHookStorageSlot())
    with pytest.raises(Exception, match="frozen"):
        tx.set_storage_updates([])


def test_from_bytes_round_trip(mock_client, hook_id, storage_updates):
    original = HookStoreTransaction(hook_id=hook_id, storage_updates=storage_updates).freeze_with(mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, HookStoreTransaction)
    assert restored.hook_id == hook_id
    assert restored.storage_updates == storage_updates
    assert restored.to_bytes() == original_bytes


def test_hook_store_transaction_can_execute(hook_id, storage_updates):
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        )
    )

    with mock_hedera_servers([[ok_response, receipt_response]]) as client:
        receipt = HookStoreTransaction(hook_id=hook_id, storage_updates=storage_updates).execute(client)

    assert receipt.status == ResponseCode.SUCCESS
