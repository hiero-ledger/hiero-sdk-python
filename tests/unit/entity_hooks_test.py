"""Unit tests for HIP-1195 hooks on account and contract create/update transactions."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_update_transaction import ContractUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hooks.evm_hook import EvmHook
from hiero_sdk_python.hooks.evm_hook_storage_update import EvmHookStorageSlot
from hiero_sdk_python.hooks.hook_creation_details import HookCreationDetails
from hiero_sdk_python.transaction.transaction import Transaction


pytestmark = pytest.mark.unit

HOOK_CONTRACT = ContractId(0, 0, 900)


def hook(hook_id, admin_key=None):
    return HookCreationDetails(
        hook_id=hook_id,
        evm_hook=EvmHook(contract_id=HOOK_CONTRACT, storage_updates=[EvmHookStorageSlot(b"\x01", b"\x01")]),
        admin_key=admin_key,
    )


def account_create():
    return AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519().public_key())


def contract_create():
    return ContractCreateTransaction().set_bytecode(b"\x60\x80").set_gas(100_000)


def account_update():
    return AccountUpdateTransaction().set_account_id(AccountId(0, 0, 55))


def contract_update():
    return ContractUpdateTransaction().set_contract_id(ContractId(0, 0, 66))


def body_of(tx, mock_account_ids):
    operator_id, _, node_account_id, _, _ = mock_account_ids
    tx.operator_account_id = operator_id
    tx.set_node_account_ids([node_account_id])
    body = tx.build_transaction_body()
    return getattr(body, body.WhichOneof("data"))


# --- Create transactions ---------------------------------------------------------------

CREATE_FACTORIES = [
    pytest.param(account_create, "cryptoCreateAccount", id="account_create"),
    pytest.param(contract_create, "contractCreateInstance", id="contract_create"),
]


@pytest.mark.parametrize(("factory", "_field"), CREATE_FACTORIES)
def test_create_defaults_to_no_hooks(mock_account_ids, factory, _field):
    tx = factory()

    assert tx.hooks == []
    assert len(body_of(tx, mock_account_ids).hook_creation_details) == 0


@pytest.mark.parametrize(("factory", "field"), CREATE_FACTORIES)
def test_create_add_and_set_hooks(mock_account_ids, factory, field):
    admin_key = PrivateKey.generate_ed25519().public_key()
    tx = factory()

    assert tx.add_hook(hook(1)) is tx
    tx.add_hook(hook(2, admin_key))

    body = body_of(tx, mock_account_ids)
    assert [h.hook_id for h in body.hook_creation_details] == [1, 2]
    assert body.hook_creation_details[0].evm_hook.spec.contract_id.contractNum == 900
    assert body.hook_creation_details[1].HasField("admin_key")

    assert tx.set_hooks([hook(7)]) is tx
    assert [h.hook_id for h in tx.hooks] == [7]


@pytest.mark.parametrize(("factory", "_field"), CREATE_FACTORIES)
def test_create_hook_validation(factory, _field):
    tx = factory()

    with pytest.raises(TypeError):
        tx.add_hook(EvmHook(contract_id=HOOK_CONTRACT))
    with pytest.raises(TypeError):
        tx.set_hooks(hook(1))
    with pytest.raises(TypeError):
        tx.set_hooks([hook(1), None])


@pytest.mark.parametrize(("factory", "_field"), CREATE_FACTORIES)
def test_create_set_hooks_copies_list(factory, _field):
    hooks = [hook(1)]
    tx = factory().set_hooks(hooks)

    hooks.append(hook(2))

    assert len(tx.hooks) == 1


@pytest.mark.parametrize(("factory", "_field"), CREATE_FACTORIES)
def test_create_hooks_round_trip(mock_client, factory, _field):
    hooks = [hook(1), hook(2, PrivateKey.generate_ed25519().public_key())]
    original = factory().set_hooks(hooks).freeze_with(mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert type(restored) is type(original)
    assert restored.hooks == hooks
    assert restored.to_bytes() == original_bytes


@pytest.mark.parametrize(("factory", "_field"), CREATE_FACTORIES)
def test_create_frozen_rejects_hook_changes(mock_client, factory, _field):
    tx = factory().freeze_with(mock_client)

    with pytest.raises(Exception, match="frozen"):
        tx.add_hook(hook(1))
    with pytest.raises(Exception, match="frozen"):
        tx.set_hooks([])


def test_account_create_hooks_in_scheduled_body():
    scheduled = account_create().add_hook(hook(3)).build_scheduled_body()

    assert scheduled.cryptoCreateAccount.hook_creation_details[0].hook_id == 3


def test_contract_create_hooks_in_scheduled_body():
    scheduled = contract_create().add_hook(hook(3)).build_scheduled_body()

    assert scheduled.contractCreateInstance.hook_creation_details[0].hook_id == 3


# --- Update transactions ---------------------------------------------------------------

UPDATE_FACTORIES = [
    pytest.param(account_update, id="account_update"),
    pytest.param(contract_update, id="contract_update"),
]


@pytest.mark.parametrize("factory", UPDATE_FACTORIES)
def test_update_defaults_to_no_hook_changes(mock_account_ids, factory):
    tx = factory()
    body = body_of(tx, mock_account_ids)

    assert tx.hooks_to_create == [] and tx.hooks_to_delete == []
    assert len(body.hook_creation_details) == 0
    assert len(body.hook_ids_to_delete) == 0


@pytest.mark.parametrize("factory", UPDATE_FACTORIES)
def test_update_add_and_set_hook_changes(mock_account_ids, factory):
    tx = factory()

    assert tx.add_hook_to_create(hook(1)) is tx
    assert tx.add_hook_to_delete(4) is tx
    tx.add_hook_to_delete(5)

    body = body_of(tx, mock_account_ids)
    assert [h.hook_id for h in body.hook_creation_details] == [1]
    assert list(body.hook_ids_to_delete) == [4, 5]

    assert tx.set_hooks_to_create([hook(8), hook(9)]) is tx
    assert tx.set_hooks_to_delete([1]) is tx
    assert [h.hook_id for h in tx.hooks_to_create] == [8, 9]
    assert tx.hooks_to_delete == [1]


@pytest.mark.parametrize("factory", UPDATE_FACTORIES)
def test_update_hook_validation(factory):
    tx = factory()

    with pytest.raises(TypeError):
        tx.add_hook_to_create(None)
    with pytest.raises(TypeError):
        tx.set_hooks_to_create([1])
    with pytest.raises(TypeError):
        tx.add_hook_to_delete("1")
    with pytest.raises(TypeError):
        tx.add_hook_to_delete(True)
    with pytest.raises(TypeError):
        tx.set_hooks_to_delete(1)
    with pytest.raises(TypeError):
        tx.set_hooks_to_delete([1, "2"])


@pytest.mark.parametrize("factory", UPDATE_FACTORIES)
def test_update_frozen_rejects_hook_changes(mock_client, factory):
    tx = factory().freeze_with(mock_client)

    for call in (
        lambda: tx.add_hook_to_create(hook(1)),
        lambda: tx.set_hooks_to_create([]),
        lambda: tx.add_hook_to_delete(1),
        lambda: tx.set_hooks_to_delete([]),
    ):
        with pytest.raises(Exception, match="frozen"):
            call()


def test_contract_update_hook_changes_round_trip(mock_client):
    original = (
        contract_update()
        .set_hooks_to_create([hook(1), hook(2, PrivateKey.generate_ed25519().public_key())])
        .set_hooks_to_delete([3, 4])
        .freeze_with(mock_client)
    )
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, ContractUpdateTransaction)
    assert restored.hooks_to_create == original.hooks_to_create
    assert restored.hooks_to_delete == [3, 4]
    assert restored.to_bytes() == original_bytes


def test_account_update_hook_changes_in_scheduled_body():
    scheduled = account_update().add_hook_to_create(hook(1)).add_hook_to_delete(2).build_scheduled_body()

    assert scheduled.cryptoUpdateAccount.hook_creation_details[0].hook_id == 1
    assert list(scheduled.cryptoUpdateAccount.hook_ids_to_delete) == [2]
