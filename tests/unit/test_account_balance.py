"""Tests for the AccountBalance class."""

import pytest

from hiero_sdk_python.account.account_balance import AccountBalance
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit


def test_account_balance_str_with_hbars_only():
    """Test __str__ method with only hbars."""
    hbars = Hbar(10)
    account_balance = AccountBalance(hbars=hbars)
    
    result = str(account_balance)
    
    assert "💰 HBAR Balance:" in result
    assert "10.00000000 ℏ" in result
    assert " hbars" in result
    # Should not include token balances section when empty
    assert "💎 Token Balances:" not in result


def test_account_balance_str_with_token_balances():
    """Test __str__ method with hbars and token balances."""
    hbars = Hbar(10)
    token_id_1 = TokenId(0, 0, 100)
    token_id_2 = TokenId(0, 0, 200)
    token_balances = {token_id_1: 1000, token_id_2: 500}
    account_balance = AccountBalance(hbars=hbars, token_balances=token_balances)
    
    result = str(account_balance)
    
    assert "💰 HBAR Balance:" in result
    assert "10.00000000 ℏ" in result
    assert " hbars" in result
    assert "💎 Token Balances:" in result
    assert " - Token ID 0.0.100: 1000 units" in result
    assert " - Token ID 0.0.200: 500 units" in result


def test_account_balance_str_with_empty_token_balances():
    """Test __str__ method with empty token balances dict."""
    hbars = Hbar(5.5)
    account_balance = AccountBalance(hbars=hbars, token_balances={})
    
    result = str(account_balance)
    
    assert "💰 HBAR Balance:" in result
    assert "5.50000000 ℏ" in result
    assert " hbars" in result
    # Should not include token balances section when empty
    assert "💎 Token Balances:" not in result


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
    account_balance = AccountBalance(hbars=hbars, token_balances=token_balances)
    
    result = repr(account_balance)
    
    assert "AccountBalance" in result
    assert "hbars=" in result
    assert "token_balances=" in result
    assert "0.0.100" in result or "TokenId" in result
    assert "1000" in result
    assert "500" in result

