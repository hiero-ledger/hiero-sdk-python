"""
Example demonstrating HIP-1195 hooks on an account.

1. Deploy a contract that implements an account allowance hook.
2. Create an account with that hook installed (AccountCreateTransaction.add_hook).
3. Write to the hook's storage (HookStoreTransaction).
4. Add a second hook and delete the first (AccountUpdateTransaction).

Hooks must be enabled on the network (`hooks.hooksEnabled=true`). If they are not,
the example says so and exits without error.

uv run examples/hooks/account_hooks.py
python examples/hooks/account_hooks.py
"""

import sys

from dotenv import load_dotenv

from examples.contract.contracts import CONTRACT_DEPLOY_GAS, HIERO_HOOK_CONTRACT_BYTECODE
from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountUpdateTransaction,
    Client,
    ContractCreateTransaction,
    EvmHook,
    EvmHookMappingEntries,
    EvmHookMappingEntry,
    EvmHookStorageSlot,
    Hbar,
    HookCreationDetails,
    HookEntityId,
    HookExtensionPoint,
    HookId,
    HookStoreTransaction,
    PrecheckError,
    PrivateKey,
    ResponseCode,
)


load_dotenv()


def setup_client() -> Client:
    """Set up the client from the environment."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def check(receipt, action):
    """Exit cleanly if hooks are disabled, exit with an error on any other failure."""
    status = ResponseCode(receipt.status)
    if status == ResponseCode.HOOKS_NOT_ENABLED:
        print("Hooks are not enabled on this network; skipping the rest of the example.")
        sys.exit(0)
    if status != ResponseCode.SUCCESS:
        print(f"{action} failed with status: {status.name}")
        sys.exit(1)
    print(f"{action}: SUCCESS")
    return receipt


def execute(transaction, client, action):
    """Execute a transaction, treating a HOOKS_NOT_ENABLED precheck like a receipt status."""
    try:
        receipt = transaction.execute(client)
    except PrecheckError as error:
        if error.status == ResponseCode.HOOKS_NOT_ENABLED:
            print("Hooks are not enabled on this network; skipping the rest of the example.")
            sys.exit(0)
        raise
    return check(receipt, action)


def deploy_hook_contract(client):
    """Deploy the always-allow account allowance hook contract."""
    receipt = execute(
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(HIERO_HOOK_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS),
        client,
        "Deploy hook contract",
    )
    print(f"Hook contract ID: {receipt.contract_id}")
    return receipt.contract_id


def create_account_with_hook(client, hook_contract_id):
    """Create an account with hook number 1 installed, with one initial storage slot."""
    account_key = PrivateKey.generate_ed25519()
    hook = HookCreationDetails(
        extension_point=HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK,
        hook_id=1,
        evm_hook=EvmHook(
            contract_id=hook_contract_id,
            storage_updates=[EvmHookStorageSlot(key=b"\x01", value=b"\x01")],
        ),
    )

    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(account_key.public_key())
        .set_initial_balance(Hbar(10))
        .add_hook(hook)
    )
    transaction.transaction_fee = Hbar(20)
    receipt = execute(transaction.freeze_with(client).sign(account_key), client, "Create account with hook")
    print(f"Account ID: {receipt.account_id}")
    return receipt.account_id, account_key


def store_hook_storage(client, account_id, account_key):
    """Update the hook's storage: one raw slot and one Solidity mapping entry."""
    hook_id = HookId(HookEntityId(account_id=account_id), 1)
    transaction = (
        HookStoreTransaction()
        .set_hook_id(hook_id)
        .add_storage_update(EvmHookStorageSlot(key=b"\x01", value=b"\x02"))
        .add_storage_update(
            EvmHookMappingEntries(
                mapping_slot=b"\x02",
                entries=[EvmHookMappingEntry.with_key(key=b"\x0a", value=b"\x0b")],
            )
        )
    )
    # The hook has no admin key, so the owning account signs.
    execute(transaction.freeze_with(client).sign(account_key), client, "Hook store")


def replace_hook(client, account_id, account_key, hook_contract_id):
    """Add hook number 2 and delete hook number 1 in one update."""
    transaction = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .add_hook_to_create(HookCreationDetails(hook_id=2, evm_hook=EvmHook(contract_id=hook_contract_id)))
        .add_hook_to_delete(1)
    )
    execute(transaction.freeze_with(client).sign(account_key), client, "Add hook 2 and delete hook 1")


def main():
    client = setup_client()
    hook_contract_id = deploy_hook_contract(client)
    account_id, account_key = create_account_with_hook(client, hook_contract_id)
    store_hook_storage(client, account_id, account_key)
    replace_hook(client, account_id, account_key, hook_contract_id)
    client.close()


if __name__ == "__main__":
    main()
