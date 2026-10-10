"""
Unit tests for MirrorNodeAccountBalance.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_mirror_node_balance import (
    MirrorNodeAccountBalance,
)
from hiero_sdk_python.hbar import Hbar


def test_init_rejects_none():
    """Test that initialization rejects None as the HBAR balance."""
    with pytest.raises(
        ValueError,
        match="hbars must be an instance of Hbar",
    ):
        MirrorNodeAccountBalance(None)


def test_init_rejects_non_hbar():
    """Test that initialization rejects values that are not Hbar instances."""
    with pytest.raises(
        ValueError,
        match="hbars must be an instance of Hbar",
    ):
        MirrorNodeAccountBalance(100)


def test_init_with_hbar():
    """Test that initialization stores the provided HBAR balance."""
    hbars = Hbar.from_tinybars(100)

    result = MirrorNodeAccountBalance(hbars)

    assert result.hbars == hbars


def test_from_json_returns_none_for_empty_balances():
    """Test that _from_json returns None when the balances array is empty."""
    root = {"balances": []}

    result = MirrorNodeAccountBalance._from_json(root)

    assert result is None


def test_from_json_returns_balance_for_account_with_hbar():
    """Test that _from_json returns the account balance when HBAR is present."""
    root = {
        "balances": [
            {
                "balance": 100,
            }
        ]
    }

    result = MirrorNodeAccountBalance._from_json(root)

    assert result is not None
    assert result.hbars == Hbar.from_tinybars(100)


def test_from_json_returns_zero_balance_for_account_with_no_hbar():
    """Test that _from_json returns a zero HBAR balance for an existing account with no HBAR."""
    root = {
        "balances": [
            {
                "balance": 0,
            }
        ]
    }

    result = MirrorNodeAccountBalance._from_json(root)

    assert result is not None
    assert result.hbars == Hbar.from_tinybars(0)


def test_from_json_rejects_non_dict_root():
    """Test that _from_json rejects a root value that is not a dictionary."""
    with pytest.raises(
        TypeError,
        match="root is not an object",
    ):
        MirrorNodeAccountBalance._from_json([])


def test_from_json_rejects_missing_balances():
    """Test that _from_json rejects a response without a balances field."""
    with pytest.raises(
        ValueError,
        match="no `balances` array",
    ):
        MirrorNodeAccountBalance._from_json({})


def test_from_json_rejects_non_list_balances():
    """Test that _from_json rejects a balances field that is not a list."""
    with pytest.raises(
        ValueError,
        match="`balances` is not an array",
    ):
        MirrorNodeAccountBalance._from_json({"balances": {}})


def test_from_json_rejects_non_dict_balance_entry():
    """Test that _from_json rejects a balance entry that is not a dictionary."""
    with pytest.raises(
        ValueError,
        match="balances entry is not an object",
    ):
        MirrorNodeAccountBalance._from_json({"balances": [100]})


def test_from_json_rejects_missing_balance_field():
    """Test that _from_json rejects a balance entry without a balance field."""
    with pytest.raises(
        ValueError,
        match="balances entry has no `balance` field",
    ):
        MirrorNodeAccountBalance._from_json({"balances": [{}]})


def test_hbars_returns_hbars():
    """Test that the hbars property returns the stored HBAR balance."""
    hbars = Hbar.from_tinybars(100)
    balance = MirrorNodeAccountBalance(hbars)

    assert balance.hbars == hbars


def test_str_returns_expected_string():
    """Test that the string representation contains the expected HBAR balance."""
    hbars = Hbar.from_tinybars(100)

    result = MirrorNodeAccountBalance(hbars)

    assert str(result) == f"MirrorNodeAccountBalance(hbars={hbars})"
