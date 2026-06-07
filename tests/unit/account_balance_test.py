"""Tests for the AccountBalance class."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_balance import AccountBalance
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenBalance
from hiero_sdk_python.hapi.services.crypto_get_account_balance_pb2 import CryptoGetAccountBalanceResponse
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


def test_account_balance_str_with_hbars_only():
    """Test __str__ method with only hbars."""
    hbars = Hbar(10)
    account_balance = AccountBalance(hbars=hbars)

    result = str(account_balance)

    assert "HBAR Balance:" in result
    assert "10.00000000 ℏ" in result
    assert "hbars" in result
    # Should not include token balances section when empty
    assert "Token Balances:" not in result


def test_account_balance_str_with_token_balances_and_decimal():
    """Test __str__ method with hbars and token balances and decimals."""
    hbars = Hbar(10)
    token_id_1 = TokenId(0, 0, 100)
    token_id_2 = TokenId(0, 0, 200)
    token_balances = {token_id_1: 1000, token_id_2: 500}
    token_decimals = {token_id_1: 1, token_id_2: 2}
    account_balance = AccountBalance(hbars=hbars, token_balances=token_balances, token_decimals=token_decimals)

    result = str(account_balance)

    assert "HBAR Balance:" in result
    assert "10.00000000 ℏ" in result
    assert " hbars" in result
    assert "Token Balances:" in result
    assert " - Token ID 0.0.100: 1000 units" in result
    assert " - Token ID 0.0.200: 500 units" in result
    assert "Token Decimals:" in result
    assert " - Token ID 0.0.100: 1 decimals" in result
    assert " - Token ID 0.0.200: 2 decimals" in result


def test_account_balance_str_with_empty_token_balances_and_decimals():
    """Test __str__ method with empty token balances and decimals dict."""
    hbars = Hbar(5.5)
    account_balance = AccountBalance(hbars=hbars, token_balances={})

    result = str(account_balance)

    assert "HBAR Balance:" in result
    assert "5.50000000 ℏ" in result
    assert " hbars" in result
    # Should not include token balances section when empty
    assert "Token Balances:" not in result
    assert "Token Decimals:" not in result


def test_account_balance_repr_with_hbars_only():
    """Test __repr__ method with only hbars."""
    hbars = Hbar(10)
    account_balance = AccountBalance(hbars=hbars)

    result = repr(account_balance)

    assert "AccountBalance" in result
    assert "hbars=" in result
    assert "token_balances={}" in result
    assert "Hbar(" in result


def test_account_balance_repr_with_token_balances():
    """Test __repr__ method with hbars and token balances."""
    hbars = Hbar(10)
    token_id_1 = TokenId(0, 0, 100)
    token_id_2 = TokenId(0, 0, 200)
    token_balances = {token_id_1: 1000, token_id_2: 500}
    token_decimals = {token_id_1: 1, token_id_2: 2}
    account_balance = AccountBalance(hbars=hbars, token_balances=token_balances, token_decimals=token_decimals)

    result = repr(account_balance)

    assert "AccountBalance" in result
    assert "hbars=" in result
    assert "token_balances=" in result
    assert "0.0.100" in result or "TokenId" in result
    assert "1000" in result
    assert "500" in result
    assert "token_decimals=" in result
    assert "1" in result
    assert "2" in result


def test_create_account_balance_from_proto():
    token_blances_proto = [
        TokenBalance(tokenId=TokenId(0, 0, 100)._to_proto(), balance=100, decimals=1),
        TokenBalance(tokenId=TokenId(0, 0, 102)._to_proto(), balance=0, decimals=0),
    ]

    proto = CryptoGetAccountBalanceResponse(
        accountID=AccountId(0, 0, 1)._to_proto(), balance=10, tokenBalances=token_blances_proto
    )

    account_balance = AccountBalance._from_proto(proto=proto)

    assert account_balance is not None
    assert account_balance.hbars.to_tinybars() == 10

    assert len(account_balance.token_balances) == 2
    assert account_balance.token_balances == {TokenId(0, 0, 100): 100, TokenId(0, 0, 102): 0}

    assert len(account_balance.token_decimals) == 2
    assert account_balance.token_decimals == {TokenId(0, 0, 100): 1, TokenId(0, 0, 102): 0}
