"""
Integration tests for HIP-1195 hooks.

Hooks are disabled by default on consensus nodes (`hooks.hooksEnabled=false`) and
the solo network used in CI does not turn them on, so these tests are skipped
unless HOOKS_ENABLED=true is set. The JS, Java and Go SDKs skip their hook
integration tests for the same reason.
"""

from __future__ import annotations

import os

import pytest

from examples.contract.contracts import CONTRACT_DEPLOY_GAS, HIERO_HOOK_CONTRACT_BYTECODE
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hooks.evm_hook import EvmHook
from hiero_sdk_python.hooks.evm_hook_call import EvmHookCall
from hiero_sdk_python.hooks.evm_hook_mapping_entry import EvmHookMappingEntry
from hiero_sdk_python.hooks.evm_hook_storage_update import EvmHookMappingEntries, EvmHookStorageSlot
from hiero_sdk_python.hooks.fungible_hook_call import FungibleHookCall
from hiero_sdk_python.hooks.fungible_hook_type import FungibleHookType
from hiero_sdk_python.hooks.hook_creation_details import HookCreationDetails
from hiero_sdk_python.hooks.hook_entity_id import HookEntityId
from hiero_sdk_python.hooks.hook_id import HookId
from hiero_sdk_python.hooks.hook_store_transaction import HookStoreTransaction
from hiero_sdk_python.hooks.nft_hook_call import NftHookCall
from hiero_sdk_python.hooks.nft_hook_type import NftHookType
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils import Account, IntegrationTestEnv, create_fungible_token, create_nft_token


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("HOOKS_ENABLED", "").lower() != "true",
        reason="Hooks are disabled on solo; set HOOKS_ENABLED=true to run against a hooks-enabled network",
    ),
]

HOOK_ID = 1
HOOK_GAS_LIMIT = 50_000


def with_fee(transaction, fee=Hbar(10)):
    """Sets a max transaction fee high enough to cover hook gas."""
    transaction.transaction_fee = fee
    return transaction


def assert_success(receipt, action):
    assert receipt.status == ResponseCode.SUCCESS, f"{action} failed with {ResponseCode(receipt.status).name}"


@pytest.fixture(scope="module")
def hook_contract_id(env):
    """Deploys the always-allow hook contract once for the module."""
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(HIERO_HOOK_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS)
        .execute(env.client)
    )
    assert_success(receipt, "Hook contract deployment")
    return receipt.contract_id


@pytest.fixture(scope="module")
def env():
    """Module-scoped environment so the hook contract is deployed once."""
    integration_env = IntegrationTestEnv()
    yield integration_env
    integration_env.close()


def hook_details(contract_id, hook_id=HOOK_ID, admin_key=None, storage_updates=None):
    return HookCreationDetails(
        hook_id=hook_id,
        evm_hook=EvmHook(contract_id=contract_id, storage_updates=storage_updates or []),
        admin_key=admin_key,
    )


def create_account_with_hook(env, contract_id, initial_hbar=10, admin_key=None) -> Account:
    key = PrivateKey.generate_ed25519()
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(key.public_key())
        .set_initial_balance(Hbar(initial_hbar))
        .add_hook(hook_details(contract_id, admin_key=admin_key))
    )
    receipt = with_fee(tx, Hbar(20)).freeze_with(env.client).sign(key).execute(env.client)
    assert_success(receipt, "Account create with hook")
    return Account(id=receipt.account_id, key=key)


def fungible_hook(hook_type=FungibleHookType.PRE_TX_ALLOWANCE_HOOK):
    return FungibleHookCall(hook_id=HOOK_ID, evm_hook_call=EvmHookCall(b"", HOOK_GAS_LIMIT), hook_type=hook_type)


# --- Hooks on create / update ---------------------------------------------------------------


def test_integration_account_create_with_hook(env, hook_contract_id):
    create_account_with_hook(env, hook_contract_id)


def test_integration_contract_create_with_hook(env, hook_contract_id):
    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(HIERO_HOOK_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS)
        .add_hook(hook_details(hook_contract_id))
        .execute(env.client)
    )

    assert_success(receipt, "Contract create with hook")


def test_integration_account_update_adds_and_deletes_hooks(env, hook_contract_id):
    account = create_account_with_hook(env, hook_contract_id)

    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account.id)
        .add_hook_to_create(hook_details(hook_contract_id, hook_id=2))
        .add_hook_to_delete(HOOK_ID)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert_success(receipt, "Account update with hook changes")


def test_integration_account_create_with_duplicate_hook_ids_fails(env, hook_contract_id):
    key = PrivateKey.generate_ed25519()
    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(key.public_key())
        .set_hooks([hook_details(hook_contract_id), hook_details(hook_contract_id)])
        .freeze_with(env.client)
        .sign(key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.HOOK_ID_REPEATED_IN_CREATION_DETAILS


# --- HookStoreTransaction ----------------------------------------------------------------


def test_integration_hook_store_updates_storage(env, hook_contract_id):
    account = create_account_with_hook(env, hook_contract_id)
    hook_id = HookId(HookEntityId(account_id=account.id), HOOK_ID)

    receipt = (
        HookStoreTransaction()
        .set_hook_id(hook_id)
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x02"))
        .add_storage_update(
            EvmHookMappingEntries(mapping_slot=b"\x03", entries=[EvmHookMappingEntry.with_key(b"\x04", b"\x05")])
        )
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert_success(receipt, "Hook store")


def test_integration_hook_store_with_admin_key(env, hook_contract_id):
    admin_key = PrivateKey.generate_ed25519()
    account = create_account_with_hook(env, hook_contract_id, admin_key=admin_key.public_key())

    receipt = (
        HookStoreTransaction()
        .set_hook_id(HookId(HookEntityId(account_id=account.id), HOOK_ID))
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x01"))
        .freeze_with(env.client)
        .sign(admin_key)
        .execute(env.client)
    )

    assert_success(receipt, "Hook store signed by admin key")


def test_integration_hook_store_round_trips_through_bytes(env, hook_contract_id):
    account = create_account_with_hook(env, hook_contract_id)
    tx = (
        HookStoreTransaction()
        .set_hook_id(HookId(HookEntityId(account_id=account.id), HOOK_ID))
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x03"))
        .freeze_with(env.client)
        .sign(account.key)
    )

    restored = Transaction.from_bytes(tx.to_bytes())

    assert isinstance(restored, HookStoreTransaction)
    assert_success(restored.execute(env.client), "Hook store from bytes")


def test_integration_hook_store_without_owner_signature_fails(env, hook_contract_id):
    account = create_account_with_hook(env, hook_contract_id)

    receipt = (
        HookStoreTransaction()
        .set_hook_id(HookId(HookEntityId(account_id=account.id), HOOK_ID))
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x01"))
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.INVALID_SIGNATURE


def test_integration_hook_store_unknown_hook_fails(env, hook_contract_id):
    account = create_account_with_hook(env, hook_contract_id)

    receipt = (
        HookStoreTransaction()
        .set_hook_id(HookId(HookEntityId(account_id=account.id), 999))
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x01"))
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.HOOK_NOT_FOUND


# --- Transfers with hooks -----------------------------------------------------------------


@pytest.mark.parametrize("hook_type", list(FungibleHookType))
def test_integration_hbar_transfer_with_hook(env, hook_contract_id, hook_type):
    sender = create_account_with_hook(env, hook_contract_id)

    receipt = (
        with_fee(TransferTransaction())
        .add_hbar_transfer_with_hook(sender.id, Hbar(-1), fungible_hook(hook_type))
        .add_hbar_transfer(env.operator_id, Hbar(1))
        .execute(env.client)
    )

    assert_success(receipt, f"HBAR transfer with {hook_type.name}")


def test_integration_token_transfer_with_hook(env, hook_contract_id):
    sender = create_account_with_hook(env, hook_contract_id)
    token_id = create_fungible_token(env)
    env.associate_and_transfer(sender.id, sender.key, token_id, 10)

    receipt = (
        with_fee(TransferTransaction())
        .add_token_transfer_with_hook(token_id, sender.id, -5, fungible_hook())
        .add_token_transfer(token_id, env.operator_id, 5)
        .execute(env.client)
    )

    assert_success(receipt, "Token transfer with hook")


def test_integration_nft_transfer_with_sender_hook(env, hook_contract_id):
    sender = create_account_with_hook(env, hook_contract_id)
    token_id = create_nft_token(env)
    mint = TokenMintTransaction().set_token_id(token_id).set_metadata([b"hook-nft"]).execute(env.client)
    assert_success(mint, "NFT mint")
    nft_id = NftId(token_id, mint.serial_numbers[0])
    associate = (
        TokenAssociateTransaction()
        .set_account_id(sender.id)
        .add_token_id(token_id)
        .freeze_with(env.client)
        .sign(sender.key)
        .execute(env.client)
    )
    assert_success(associate, "NFT association")
    assert_success(
        TransferTransaction().add_nft_transfer(nft_id, env.operator_id, sender.id).execute(env.client),
        "NFT transfer to sender",
    )

    receipt = (
        with_fee(TransferTransaction())
        .add_nft_transfer_with_hook(
            nft_id,
            sender.id,
            env.operator_id,
            sender_hook_call=NftHookCall(
                hook_id=HOOK_ID,
                evm_hook_call=EvmHookCall(b"", HOOK_GAS_LIMIT),
                hook_type=NftHookType.PRE_HOOK_SENDER,
            ),
        )
        .execute(env.client)
    )

    assert_success(receipt, "NFT transfer with sender hook")
