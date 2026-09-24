"""
Unit tests for MirrorNodeAccountBalance.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_mirror_node_balance import (
    MirrorNodeAccountBalance,
)
from hiero_sdk_python.hbar import Hbar


def test_init():
    hbars = Hbar.from_tinybars(100)

    balance = MirrorNodeAccountBalance(hbars)

    assert balance.hbars == hbars
    assert balance.get_hbars() == hbars


def test_init_rejects_none():
    with pytest.raises(
        ValueError,
        match="hbars cannot be None",
    ):
        MirrorNodeAccountBalance(None)


def test_from_json_returns_balance():
    root = {
        "balances": [
            {
                "balance": 100,
            }
        ]
    }

    balance = MirrorNodeAccountBalance.from_json(root)

    assert balance is not None
    assert balance.get_hbars() == Hbar.from_tinybars(100)


def test_from_json_returns_none_for_empty_balances():
    root = {"balances": []}

    balance = MirrorNodeAccountBalance.from_json(root)

    assert balance is None


def test_from_json_rejects_missing_balances():
    with pytest.raises(
        ValueError,
        match="no `balances` array",
    ):
        MirrorNodeAccountBalance.from_json({})


def test_from_json_rejects_none_balances():
    with pytest.raises(
        ValueError,
        match="no `balances` array",
    ):
        MirrorNodeAccountBalance.from_json(
            {
                "balances": None,
            }
        )


def test_from_json_rejects_non_list_balances():
    with pytest.raises(
        ValueError,
        match="is not an array",
    ):
        MirrorNodeAccountBalance.from_json(
            {
                "balances": {},
            }
        )


def test_from_json_rejects_non_object_balance_entry():
    with pytest.raises(
        ValueError,
        match="balances entry is not an object",
    ):
        MirrorNodeAccountBalance.from_json(
            {
                "balances": ["invalid"],
            }
        )


def test_from_json_rejects_missing_balance_field():
    with pytest.raises(
        ValueError,
        match="has no `balance` field",
    ):
        MirrorNodeAccountBalance.from_json({"balances": [{}]})


def test_from_json_rejects_none_balance_field():
    with pytest.raises(
        ValueError,
        match="has no `balance` field",
    ):
        MirrorNodeAccountBalance.from_json(
            {
                "balances": [
                    {
                        "balance": None,
                    }
                ]
            }
        )


def test_from_json_handles_zero_balance():
    balance = MirrorNodeAccountBalance.from_json(
        {
            "balances": [
                {
                    "balance": 0,
                }
            ]
        }
    )

    assert balance is not None
    assert balance.get_hbars() == Hbar.from_tinybars(0)


def test_str():
    hbars = Hbar.from_tinybars(100)
    balance = MirrorNodeAccountBalance(hbars)

    result = str(balance)

    assert result == f"MirrorNodeAccountBalance{{hbars={hbars}}}"
