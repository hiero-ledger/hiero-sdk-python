"""
Unit tests for MirrorNodeAccountBalanceQuery.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python import (
    AccountId,
)
from hiero_sdk_python.query.mirror_node_account_balance_query import MirrorNodeAccountBalanceQuery


def test_defaults_match_other_mirror_rest_queries():
    query = MirrorNodeAccountBalanceQuery()

    assert query.get_account_id() is None
    assert query.get_max_attempts() == 10
    assert query.get_max_backoff() == 8.0


def test_setters_are_fluent_and_round_trip():
    account_id = AccountId.from_string("0.0.5005")

    query = MirrorNodeAccountBalanceQuery().set_account_id(account_id).set_max_attempts(3).set_max_backoff(0.5)

    assert query.get_account_id() == account_id
    assert query.get_max_attempts() == 3
    assert query.get_max_backoff() == 0.5


def test_set_account_id_rejects_none():
    with pytest.raises(
        ValueError,
        match="account_id must not be None",
    ):
        MirrorNodeAccountBalanceQuery().set_account_id(None)


def test_set_max_backoff_rejects_values_below_half_second():
    with pytest.raises(
        ValueError,
        match="at least 0.5 seconds",
    ):
        MirrorNodeAccountBalanceQuery().set_max_backoff(0.499)


def test_set_max_attempts_rejects_non_positive_values():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        MirrorNodeAccountBalanceQuery().set_max_attempts(0)


def test_to_string_includes_account_id():
    query = MirrorNodeAccountBalanceQuery().set_account_id(AccountId.from_string("0.0.5005"))

    assert "0.0.5005" in str(query)
