from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.mirror_node_token_balance_query import MirrorNodeTokenBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils import create_fungible_token, create_nft_token, wait_for_mirror_node


@pytest.mark.integration
def test_fetch_fungible_balance(env):
    """Test query balance for treasury account for fungible token, with its decimals."""
    initial_balance, decimals = 1000, 3
    token_id = create_fungible_token(
        env, [lambda tx: tx.set_decimals(decimals), lambda tx: tx.set_initial_supply(initial_balance)]
    )

    balance = wait_for_mirror_node(
        fn=lambda: (
            MirrorNodeTokenBalanceQuery().set_account_id(env.operator_id).set_token_id(token_id).execute(env.client)
        ),
        predicate=lambda bal: bal.balance == initial_balance,
    )

    assert balance.token_id == token_id
    assert balance.balance == initial_balance
    assert balance.decimals == decimals
    assert balance.associated is True


@pytest.mark.integration
def test_fetch_nft_balance(env):
    """Test query non-fungible token the balance for the account."""
    token_id = create_nft_token(env)

    TokenMintTransaction().set_token_id(token_id).set_metadata([b"Hello! Hiero"] * 3).execute(env.client)

    balance = wait_for_mirror_node(
        fn=lambda: (
            MirrorNodeTokenBalanceQuery().set_account_id(env.operator_id).set_token_id(token_id).execute(env.client)
        ),
        predicate=lambda bal: bal.balance == 3,
    )

    assert balance.token_id == token_id
    assert balance.balance == 3
    assert balance.decimals == 0
    assert balance.associated is True


@pytest.mark.integration
def test_execute_requires_both_ids(env):
    """Test that both ids are required to set before calling the execute."""
    tokenId = create_fungible_token(env)

    with pytest.raises(ValueError, match="account_id must be set before executing"):
        MirrorNodeTokenBalanceQuery().set_token_id(tokenId).execute(env.client)

    with pytest.raises(ValueError, match="token_id must be set before executing"):
        MirrorNodeTokenBalanceQuery().set_account_id(env.operator_id).execute(env.client)


def _query(env, account_id, token_id):
    """Build and execute a token balance query against the mirror node."""
    return MirrorNodeTokenBalanceQuery().set_account_id(account_id).set_token_id(token_id).execute(env.client)


@pytest.mark.integration
def test_associated_but_unfunded_account(env):
    """An associated account with no transfers reports balance 0 and associated True."""
    account = env.create_account()
    token_id = create_fungible_token(env, [lambda tx: tx.set_decimals(3)])

    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account.id)
        .add_token_id(token_id)
        .freeze_with(env.client)
        .sign(account.key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Association failed: {ResponseCode(receipt.status).name}"

    balance = wait_for_mirror_node(
        fn=lambda: _query(env, account.id, token_id),
        predicate=lambda b: b.associated,
        timeout=30,
    )

    assert balance.token_id == token_id
    assert balance.balance == 0
    assert balance.decimals == 3
    assert balance.associated is True


@pytest.mark.integration
def test_no_relationship_reports_not_associated(env):
    """An account with no relationship to the token reports zeros and associated False."""
    account = env.create_account()
    token_id = create_fungible_token(env)

    # The fresh account may 404 transiently on the mirror node; the poll absorbs that.
    balance = wait_for_mirror_node(
        fn=lambda: _query(env, account.id, token_id),
        predicate=lambda _b: True,
        timeout=30,
    )

    assert balance.balance == 0
    assert balance.decimals == 0
    assert balance.associated is False


@pytest.mark.integration
def test_unknown_account_raises_invalid_account_id(env):
    """A non-existent account fails with INVALID_ACCOUNT_ID."""
    token_id = create_fungible_token(env)

    with pytest.raises(PrecheckError) as e:
        MirrorNodeTokenBalanceQuery().set_account_id(AccountId(0, 0, 999_999_999)).set_token_id(token_id).execute(
            env.client
        )
    assert e.value.status == ResponseCode.INVALID_ACCOUNT_ID


@pytest.mark.integration
def test_fetch_balance_by_evm_address(env):
    """The account can be addressed by its (long-zero) EVM address."""
    account = env.create_account()
    token_id = create_fungible_token(env)
    env.associate_and_transfer(account.id, account.key, token_id, 40)

    evm_account_id = AccountId.from_evm_address(account.id.to_evm_address(), account.id.shard, account.id.realm)

    balance = wait_for_mirror_node(
        fn=lambda: _query(env, evm_account_id, token_id),
        predicate=lambda b: b.balance == 40,
        timeout=30,
    )

    assert balance.balance == 40
    assert balance.decimals == 2
    assert balance.associated is True


@pytest.mark.integration
def test_fetch_balance_by_alias(env):
    """The account can be addressed by its public key alias; no token relationship yields zeros."""
    token_id = create_fungible_token(env)
    key = PrivateKey.generate_ed25519()
    alias_id = AccountId(shard=0, realm=0, alias_key=key.public_key())
    amount = Hbar(1).to_tinybars()

    # Transferring HBAR to an unknown alias auto-creates the account.
    (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, -amount)
        .add_hbar_transfer(alias_id, amount)
        .freeze_with(env.client)
        .sign(env.operator_key)
        .execute(env.client)
    )

    balance = wait_for_mirror_node(
        fn=lambda: _query(env, alias_id, token_id),
        predicate=lambda _b: True,
        timeout=30,
    )

    assert balance.balance == 0
    assert balance.decimals == 0
    assert balance.associated is False


@pytest.mark.integration
def test_balance_above_2_pow_53_is_exact(env):
    """Balances above 2**53 are returned as exact ints, not rounded floats."""
    big = 9007199254740993  # 2**53 + 1, not representable as a float
    token_id = create_fungible_token(
        env,
        [
            lambda tx: tx.set_decimals(0),
            lambda tx: tx.set_initial_supply(big),
            lambda tx: tx.set_supply_type(SupplyType.INFINITE),
            lambda tx: tx.set_max_supply(0),
        ],
    )

    balance = wait_for_mirror_node(
        fn=lambda: _query(env, env.operator_id, token_id),
        predicate=lambda b: b.balance == big,
        timeout=30,
    )

    assert isinstance(balance.balance, int)
    assert balance.balance == big
    assert balance.decimals == 0
