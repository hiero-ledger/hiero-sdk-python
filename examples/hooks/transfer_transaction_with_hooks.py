"""
Example demonstrating HIP-1195 hooks on transfers.

1. Deploy a contract that implements an account allowance hook.
2. Create an account with that hook installed.
3. Send HBAR from the account, calling its hook once before the transfer.
4. Send HBAR again, calling its hook before and after the transfer.

The hook contract used here always allows the transfer. A real hook would check
the proposed transfers and the call data, and could let a transfer through
without the account's signature.

Hooks must be enabled on the network (`hooks.hooksEnabled=true`). If they are not,
the example says so and exits without error.

uv run examples/hooks/transfer_transaction_with_hooks.py
python examples/hooks/transfer_transaction_with_hooks.py
"""

import sys

from dotenv import load_dotenv

from examples.contract.contracts import CONTRACT_DEPLOY_GAS, HIERO_HOOK_CONTRACT_BYTECODE
from hiero_sdk_python import (
    AccountCreateTransaction,
    Client,
    ContractCreateTransaction,
    EvmHook,
    EvmHookCall,
    FungibleHookCall,
    FungibleHookType,
    Hbar,
    HookCreationDetails,
    PrecheckError,
    PrivateKey,
    ResponseCode,
    TransferTransaction,
)


load_dotenv()

HOOK_ID = 1
HOOK_GAS_LIMIT = 50_000


def setup_client() -> Client:
    """Set up the client from the environment."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def execute(transaction, client, action):
    """Execute a transaction; exit cleanly if hooks are disabled, with an error on any other failure."""
    try:
        receipt = transaction.execute(client)
    except PrecheckError as error:
        if error.status == ResponseCode.HOOKS_NOT_ENABLED:
            print("Hooks are not enabled on this network; skipping the rest of the example.")
            sys.exit(0)
        raise

    status = ResponseCode(receipt.status)
    if status == ResponseCode.HOOKS_NOT_ENABLED:
        print("Hooks are not enabled on this network; skipping the rest of the example.")
        sys.exit(0)
    if status != ResponseCode.SUCCESS:
        print(f"{action} failed with status: {status.name}")
        sys.exit(1)
    print(f"{action}: SUCCESS")
    return receipt


def create_account_with_hook(client):
    """Deploy the hook contract and create an account with the hook installed."""
    contract_receipt = execute(
        ContractCreateTransaction()
        .set_bytecode(bytes.fromhex(HIERO_HOOK_CONTRACT_BYTECODE))
        .set_gas(CONTRACT_DEPLOY_GAS),
        client,
        "Deploy hook contract",
    )

    account_key = PrivateKey.generate_ed25519()
    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(account_key.public_key())
        .set_initial_balance(Hbar(10))
        .add_hook(HookCreationDetails(hook_id=HOOK_ID, evm_hook=EvmHook(contract_id=contract_receipt.contract_id)))
    )
    transaction.transaction_fee = Hbar(20)
    receipt = execute(transaction.freeze_with(client).sign(account_key), client, "Create account with hook")
    print(f"Account ID: {receipt.account_id}")
    return receipt.account_id


def transfer_with_hook(client, account_id, hook_type):
    """Send 1 HBAR from the account to the operator, calling the account's hook."""
    hook_call = FungibleHookCall(
        hook_id=HOOK_ID,
        evm_hook_call=EvmHookCall(data=b"", gas_limit=HOOK_GAS_LIMIT),
        hook_type=hook_type,
    )
    transaction = (
        TransferTransaction()
        .add_hbar_transfer_with_hook(account_id, Hbar(-1), hook_call)
        .add_hbar_transfer(client.operator_account_id, Hbar(1))
    )
    transaction.transaction_fee = Hbar(10)
    execute(transaction, client, f"HBAR transfer with {hook_type.name}")


def main():
    client = setup_client()
    account_id = create_account_with_hook(client)
    transfer_with_hook(client, account_id, FungibleHookType.PRE_TX_ALLOWANCE_HOOK)
    transfer_with_hook(client, account_id, FungibleHookType.PRE_POST_TX_ALLOWANCE_HOOK)
    client.close()


if __name__ == "__main__":
    main()
