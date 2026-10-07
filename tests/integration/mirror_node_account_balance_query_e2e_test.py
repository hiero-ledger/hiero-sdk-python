"""
Integration tests for MirrorNodeAccountBalanceQuery.

These tests verify the mirror-node REST replacement for
CryptoGetAccountBalanceQuery.

The mirror node is eventually consistent, so balance assertions
after transactions wait until the expected balance is visible.
"""

from __future__ import annotations

import pytest

from examples.contract.contracts.contract_utils import CONTRACT_DEPLOY_GAS, SIMPLE_CONTRACT_BYTECODE
from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Hbar,
    PrivateKey,
    TransferTransaction,
)
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.query.mirror_node_account_balance_query import (
    MirrorNodeAccountBalanceQuery,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import wait_for_mirror_node


def require_operator_balance(env, amount: Hbar) -> None:
    balance = MirrorNodeAccountBalanceQuery(env.client.operator_account_id).execute(env.client)

    if balance is None or balance.hbars < amount:
        pytest.skip(f"Operator account does not have enough HBAR for this test: requires {amount}")


def test_can_fetch_balance_for_client_operator(env):
    """
    Can fetch the HBAR balance for the client operator.
    """
    operator_id = env.client.operator_account_id
    query = MirrorNodeAccountBalanceQuery(operator_id)
    balance = query.execute(env.client)

    assert balance is not None
    assert balance.hbars.to_tinybars() > 0


def test_can_fetch_balance_by_evm_address(env):
    """
    Can fetch the HBAR balance for an account addressed by its
    EVM address.
    """
    initial_balance = Hbar(1)
    require_operator_balance(env, initial_balance)

    key = PrivateKey.generate_ecdsa()

    receipt = (
        AccountCreateTransaction(
            key=key.public_key(),
            initial_balance=initial_balance,
        )
        .freeze_with(env.client)
        .sign(env.client.operator_private_key)
        .execute(env.client)
    )

    account_id = receipt.account_id

    assert account_id is not None

    evm_address = account_id.to_evm_address()

    evm_address_account_id = AccountId.from_evm_address(
        evm_address,
        account_id.shard,
        account_id.realm,
    )

    balance = wait_for_mirror_node(
        fn=lambda: MirrorNodeAccountBalanceQuery(evm_address_account_id).execute(env.client),
        predicate=lambda bal: bal.hbars == initial_balance,
    )

    assert balance.hbars == initial_balance


def test_can_fetch_balance_by_alias(env):
    """
    Can fetch the HBAR balance for an account addressed by its
    public key alias.
    """
    client = env.client
    initial_balance = Hbar(1)

    require_operator_balance(env, initial_balance)

    key = PrivateKey.generate_ed25519()

    alias_account_id = AccountId(
        shard=0,
        realm=0,
        alias_key=key.public_key(),
    )

    (
        TransferTransaction()
        .add_hbar_transfer(
            client.operator_account_id,
            -initial_balance.to_tinybars(),
        )
        .add_hbar_transfer(
            alias_account_id,
            initial_balance.to_tinybars(),
        )
        .freeze_with(client)
        .sign(client.operator_private_key)
        .execute(client)
    )

    balance = wait_for_mirror_node(
        fn=lambda: MirrorNodeAccountBalanceQuery(alias_account_id).execute(env.client),
        predicate=lambda bal: bal.hbars == initial_balance,
    )

    assert balance.hbars == initial_balance


@pytest.mark.parametrize(
    "account_id",
    [
        AccountId(0, 0, 999_999_999),
        AccountId(1, 0, 100),
        AccountId(0, 1, 100),
        AccountId(1, 1, 100),
    ],
)
def test_throws_invalid_account_id_for_non_existent_account(env, account_id):
    """
    Fails with INVALID_ACCOUNT_ID for a non-existent account.
    """
    client = env.client

    with pytest.raises(PrecheckError) as e:
        MirrorNodeAccountBalanceQuery(account_id).execute(client)
    assert e.value.status == ResponseCode.INVALID_ACCOUNT_ID


def test_can_fetch_balance_for_contract(env):
    """
    Can fetch the HBAR balance of a contract passed as an account ID.
    """
    client = env.client
    contract_id = create_test_contract(env)

    contract_as_account_id = AccountId(
        contract_id.shard,
        contract_id.realm,
        contract_id.contract,
    )

    amount = Hbar(1)

    (
        TransferTransaction()
        .add_hbar_transfer(
            client.operator_account_id,
            -amount.to_tinybars(),
        )
        .add_hbar_transfer(
            contract_as_account_id,
            amount.to_tinybars(),
        )
        .freeze_with(client)
        .sign(client.operator_private_key)
        .execute(client)
    )

    balance = wait_for_mirror_node(
        fn=lambda: MirrorNodeAccountBalanceQuery(contract_as_account_id).execute(env.client),
        predicate=lambda bal: bal.hbars == amount,
    )

    assert balance.hbars == amount


def create_test_contract(env):
    """
    Placeholder for the SDK's existing contract integration-test helper.

    This function is currently unused because the contract test is
    skipped until the appropriate helper is available.
    """
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(SIMPLE_CONTRACT_BYTECODE)
        .set_file_memo("some test file create transaction memo")
        .execute(env.client)
    )
    file_id = receipt.file_id

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("some test contract create transaction memo")
        .execute(env.client)
    )

    return receipt.contract_id
