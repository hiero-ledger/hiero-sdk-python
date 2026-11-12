"""Unit tests for the HIP-1195 hook model classes."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2, hook_types_pb2
from hiero_sdk_python.hooks.evm_hook import EvmHook, EvmHookSpec
from hiero_sdk_python.hooks.evm_hook_call import EvmHookCall
from hiero_sdk_python.hooks.evm_hook_mapping_entry import EvmHookMappingEntry
from hiero_sdk_python.hooks.evm_hook_storage_update import (
    EvmHookMappingEntries,
    EvmHookStorageSlot,
    EvmHookStorageUpdate,
)
from hiero_sdk_python.hooks.fungible_hook_call import FungibleHookCall
from hiero_sdk_python.hooks.fungible_hook_type import FungibleHookType
from hiero_sdk_python.hooks.hook_call import HookCall
from hiero_sdk_python.hooks.hook_creation_details import HookCreationDetails
from hiero_sdk_python.hooks.hook_entity_id import HookEntityId
from hiero_sdk_python.hooks.hook_extension_point import HookExtensionPoint
from hiero_sdk_python.hooks.hook_id import HookId
from hiero_sdk_python.hooks.nft_hook_call import NftHookCall
from hiero_sdk_python.hooks.nft_hook_type import NftHookType


pytestmark = pytest.mark.unit


# --- HookExtensionPoint ---------------------------------------------------------------


def test_extension_point_matches_proto_value():
    assert HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK._to_proto() == hook_types_pb2.ACCOUNT_ALLOWANCE_HOOK
    assert HookExtensionPoint._from_proto(hook_types_pb2.ACCOUNT_ALLOWANCE_HOOK) is (
        HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK
    )


def test_extension_point_rejects_unknown_value():
    with pytest.raises(ValueError):
        HookExtensionPoint._from_proto(99)


# --- HookEntityId / HookId ------------------------------------------------------------


def test_hook_entity_id_account_round_trip():
    entity = HookEntityId(account_id=AccountId(0, 0, 5))

    proto = entity._to_proto()

    assert proto.WhichOneof("entity_id") == "account_id"
    assert entity.is_account and not entity.is_contract
    assert HookEntityId._from_proto(proto) == entity


def test_hook_entity_id_contract_round_trip():
    entity = HookEntityId(contract_id=ContractId(0, 0, 7))

    proto = entity._to_proto()

    assert proto.WhichOneof("entity_id") == "contract_id"
    assert entity.is_contract and not entity.is_account
    assert HookEntityId._from_proto(proto) == entity


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"account_id": AccountId(0, 0, 1), "contract_id": ContractId(0, 0, 1)}],
)
def test_hook_entity_id_requires_exactly_one_id(kwargs):
    with pytest.raises(ValueError, match="exactly one"):
        HookEntityId(**kwargs)


def test_hook_entity_id_rejects_wrong_types():
    with pytest.raises(TypeError):
        HookEntityId(account_id="0.0.1")
    with pytest.raises(TypeError):
        HookEntityId(contract_id=AccountId(0, 0, 1))


def test_hook_entity_id_from_empty_proto_raises():
    with pytest.raises(ValueError):
        HookEntityId._from_proto(basic_types_pb2.HookEntityId())


def test_hook_id_round_trip_and_hashable():
    hook_id = HookId(HookEntityId(account_id=AccountId(0, 0, 5)), 3)

    proto = hook_id._to_proto()

    assert proto.hook_id == 3
    assert proto.entity_id.account_id.accountNum == 5
    assert HookId._from_proto(proto) == hook_id
    assert len({hook_id, HookId(HookEntityId(account_id=AccountId(0, 0, 5)), 3)}) == 1


@pytest.mark.parametrize("bad", ["3", 3.0, True, None])
def test_hook_id_rejects_non_int_number(bad):
    with pytest.raises(TypeError):
        HookId(HookEntityId(account_id=AccountId(0, 0, 5)), bad)


def test_hook_id_rejects_non_entity():
    with pytest.raises(TypeError):
        HookId(AccountId(0, 0, 5), 1)


# --- EvmHookCall / HookCall -----------------------------------------------------------


def test_evm_hook_call_round_trip():
    call = EvmHookCall(data=bytearray(b"\x01\x02"), gas_limit=25_000)

    assert call.data == b"\x01\x02"
    assert EvmHookCall._from_proto(call._to_proto()) == call


def test_evm_hook_call_validation():
    with pytest.raises(TypeError):
        EvmHookCall(data="0x01")
    with pytest.raises(TypeError):
        EvmHookCall(gas_limit=1.5)
    with pytest.raises(ValueError):
        EvmHookCall(gas_limit=-1)


def test_hook_call_round_trip():
    call = HookCall(hook_id=2, evm_hook_call=EvmHookCall(b"\xaa", 100))

    proto = call._to_proto()

    assert proto.hook_id == 2
    assert proto.evm_hook_call.data == b"\xaa"
    assert HookCall._from_proto(proto) == call


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (HookCall(evm_hook_call=EvmHookCall()), "hook_id"),
        (HookCall(hook_id=1), "evm_hook_call"),
    ],
)
def test_hook_call_to_proto_requires_fields(call, message):
    with pytest.raises(ValueError, match=message):
        call._to_proto()


def test_hook_call_rejects_wrong_types():
    with pytest.raises(TypeError):
        HookCall(hook_id="1")
    with pytest.raises(TypeError):
        HookCall(evm_hook_call=b"\x01")


@pytest.mark.parametrize("hook_type", list(FungibleHookType))
def test_fungible_hook_call_lands_in_matching_oneof(hook_type):
    call = FungibleHookCall(hook_id=1, evm_hook_call=EvmHookCall(b"\x01", 10), hook_type=hook_type)
    account_amount = basic_types_pb2.AccountAmount()

    call._apply_to(account_amount)

    assert account_amount.WhichOneof("hook_call") == hook_type.value
    assert FungibleHookCall._from_account_amount(account_amount) == call


def test_fungible_hook_call_absent_returns_none():
    assert FungibleHookCall._from_account_amount(basic_types_pb2.AccountAmount()) is None


def test_fungible_hook_call_defaults_and_validation():
    assert FungibleHookCall().hook_type is FungibleHookType.PRE_TX_ALLOWANCE_HOOK
    with pytest.raises(TypeError):
        FungibleHookCall(hook_type=NftHookType.PRE_HOOK_SENDER)


@pytest.mark.parametrize("hook_type", list(NftHookType))
def test_nft_hook_call_lands_in_matching_oneof(hook_type):
    call = NftHookCall(hook_id=4, evm_hook_call=EvmHookCall(b"\x02", 20), hook_type=hook_type)
    nft_transfer = basic_types_pb2.NftTransfer()

    call._apply_to(nft_transfer)

    sender, receiver = NftHookCall._from_nft_transfer(nft_transfer)
    if hook_type.is_sender:
        assert nft_transfer.WhichOneof("sender_allowance_hook_call") == hook_type.value
        assert (sender, receiver) == (call, None)
    else:
        assert nft_transfer.WhichOneof("receiver_allowance_hook_call") == hook_type.value
        assert (sender, receiver) == (None, call)


def test_nft_hook_type_sides():
    assert {t for t in NftHookType if t.is_sender} == {NftHookType.PRE_HOOK_SENDER, NftHookType.PRE_POST_HOOK_SENDER}
    assert {t for t in NftHookType if t.is_receiver} == {
        NftHookType.PRE_HOOK_RECEIVER,
        NftHookType.PRE_POST_HOOK_RECEIVER,
    }


def test_nft_hook_call_validation():
    with pytest.raises(TypeError):
        NftHookCall(hook_type=FungibleHookType.PRE_TX_ALLOWANCE_HOOK)


# --- Storage updates -----------------------------------------------------------------


def test_mapping_entry_with_key_round_trip():
    entry = EvmHookMappingEntry.with_key(b"\x01", b"\x02")

    proto = entry._to_proto()

    assert proto.WhichOneof("entry_key") == "key"
    assert EvmHookMappingEntry._from_proto(proto) == entry


def test_mapping_entry_with_preimage_round_trip():
    entry = EvmHookMappingEntry.with_preimage(b"some-preimage", b"\x09")

    proto = entry._to_proto()

    assert proto.WhichOneof("entry_key") == "preimage"
    assert EvmHookMappingEntry._from_proto(proto) == entry


def test_mapping_entry_validation():
    with pytest.raises(ValueError, match="not both"):
        EvmHookMappingEntry(key=b"\x01", preimage=b"\x02")
    with pytest.raises(ValueError, match="key or a preimage"):
        EvmHookMappingEntry(value=b"\x01")._to_proto()
    with pytest.raises(ValueError):
        EvmHookMappingEntry._from_proto(hook_types_pb2.EvmHookMappingEntry())
    with pytest.raises(TypeError):
        EvmHookMappingEntry(key="01")


def test_storage_slot_round_trip():
    slot = EvmHookStorageSlot(key=b"\x01", value=b"\x02")

    proto = slot._to_proto()

    assert proto.WhichOneof("update") == "storage_slot"
    assert EvmHookStorageUpdate._from_proto(proto) == slot


def test_storage_slot_validation():
    with pytest.raises(TypeError):
        EvmHookStorageSlot(key="01")


def test_mapping_entries_round_trip():
    update = EvmHookMappingEntries(
        mapping_slot=b"\x03",
        entries=[EvmHookMappingEntry.with_key(b"\x01", b"\x02"), EvmHookMappingEntry.with_preimage(b"p")],
    )

    proto = update._to_proto()

    assert proto.WhichOneof("update") == "mapping_entries"
    assert len(proto.mapping_entries.entries) == 2
    assert EvmHookStorageUpdate._from_proto(proto) == update


def test_mapping_entries_validation():
    with pytest.raises(TypeError):
        EvmHookMappingEntries(entries=[EvmHookStorageSlot()])
    with pytest.raises(TypeError):
        EvmHookMappingEntries(mapping_slot=3)


def test_storage_update_from_empty_proto_raises():
    with pytest.raises(ValueError):
        EvmHookStorageUpdate._from_proto(hook_types_pb2.EvmHookStorageUpdate())


def test_storage_update_is_abstract():
    with pytest.raises(TypeError):
        EvmHookStorageUpdate()


# --- EvmHook / HookCreationDetails -----------------------------------------------------


def test_evm_hook_round_trip():
    hook = EvmHook(contract_id=ContractId(0, 0, 9), storage_updates=[EvmHookStorageSlot(b"\x01", b"\x01")])

    proto = hook._to_proto()

    assert proto.spec.contract_id.contractNum == 9
    assert len(proto.storage_updates) == 1
    assert EvmHook._from_proto(proto) == hook
    assert isinstance(hook, EvmHookSpec)


def test_evm_hook_validation():
    with pytest.raises(ValueError, match="contract_id"):
        EvmHook()._to_proto()
    with pytest.raises(TypeError):
        EvmHook(contract_id=AccountId(0, 0, 1))
    with pytest.raises(TypeError):
        EvmHook(contract_id=ContractId(0, 0, 1), storage_updates=[b"\x01"])


def test_hook_creation_details_round_trip_with_admin_key():
    admin_key = PrivateKey.generate_ed25519().public_key()
    details = HookCreationDetails(
        extension_point=HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK,
        hook_id=5,
        evm_hook=EvmHook(contract_id=ContractId(0, 0, 9)),
        admin_key=admin_key,
    )

    proto = details._to_proto()

    assert proto.hook_id == 5
    assert proto.HasField("admin_key")
    assert HookCreationDetails._from_proto(proto) == details


def test_hook_creation_details_without_admin_key():
    details = HookCreationDetails(hook_id=1, evm_hook=EvmHook(contract_id=ContractId(0, 0, 9)))

    proto = details._to_proto()

    assert not proto.HasField("admin_key")
    assert HookCreationDetails._from_proto(proto).admin_key is None


def test_hook_creation_details_validation():
    with pytest.raises(ValueError, match="evm_hook"):
        HookCreationDetails(hook_id=1)._to_proto()
    with pytest.raises(TypeError):
        HookCreationDetails(hook_id="1")
    with pytest.raises(TypeError):
        HookCreationDetails(extension_point=0)
    with pytest.raises(TypeError):
        HookCreationDetails(admin_key=b"key")
    with pytest.raises(TypeError):
        HookCreationDetails(evm_hook=ContractId(0, 0, 1))
