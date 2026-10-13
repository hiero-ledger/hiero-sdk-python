from __future__ import annotations

import pytest

from hiero_sdk_python.query.mirror_node_token_balance_query import MirrorNodeTokenBalanceQuery
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
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


@pytest.mark.integration
def test_execute_requires_both_ids(env):
    """Test that both ids are required to set before calling the execute."""
    tokenId = create_fungible_token(env)

    with pytest.raises(ValueError, match="account_id must be set before executing"):
        MirrorNodeTokenBalanceQuery().set_token_id(tokenId).execute(env.client)

    with pytest.raises(ValueError, match="token_id must be set before executing"):
        MirrorNodeTokenBalanceQuery().set_account_id(env.operator_id).execute(env.client)
