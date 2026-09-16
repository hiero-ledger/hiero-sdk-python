"""
Unit tests for MirrorNodeAccountBalanceQuery.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python import AccountId
from hiero_sdk_python.query.mirror_node_account_balance_query import (
    MirrorNodeAccountBalanceQuery,
)


def test_constructor_sets_account_id_and_defaults():
    account_id = AccountId.from_string("0.0.5005")

    query = MirrorNodeAccountBalanceQuery(account_id)

    assert query.get_account_id == account_id
    assert query.max_attempts == 10
    assert query.max_backoff == 8.0


def test_constructor_rejects_none_account_id():
    with pytest.raises(
        ValueError,
        match="account_id must not be None",
    ):
        MirrorNodeAccountBalanceQuery(None)


def test_setters_are_fluent_and_round_trip():
    initial_account_id = AccountId.from_string("0.0.5005")
    updated_account_id = AccountId.from_string("0.0.6006")

    query = (
        MirrorNodeAccountBalanceQuery(initial_account_id)
        .set_account_id(updated_account_id)
        .set_max_attempts(3)
        .set_max_backoff(0.5)
    )

    assert query.get_account_id == updated_account_id
    assert query.max_attempts == 3
    assert query.max_backoff == 0.5


def test_set_account_id_rejects_none():
    account_id = AccountId.from_string("0.0.5005")
    query = MirrorNodeAccountBalanceQuery(account_id)

    with pytest.raises(
        ValueError,
        match="account_id must not be None",
    ):
        query.set_account_id(None)


def test_set_account_id_rejects_invalid_type():
    account_id = AccountId.from_string("0.0.5005")
    query = MirrorNodeAccountBalanceQuery(account_id)

    with pytest.raises(
        TypeError,
        match="account_id must be an AccountId instance",
    ):
        query.set_account_id("0.0.6006")


def test_set_max_attempts_rejects_zero():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        query.set_max_attempts(0)


def test_set_max_attempts_rejects_negative():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        query.set_max_attempts(-1)


def test_set_max_attempts_rejects_non_integer():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        TypeError,
        match="max_attempts must be an integer",
    ):
        query.set_max_attempts(3.5)


def test_set_max_backoff_rejects_values_below_half_second():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="at least 0.5 seconds",
    ):
        query.set_max_backoff(0.499)


def test_set_max_backoff_rejects_negative():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="at least 0.5 seconds",
    ):
        query.set_max_backoff(-1)


def test_set_max_backoff_rejects_non_numeric():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        TypeError,
        match="not supported between instances of 'str' and 'float'",
    ):
        query.set_max_backoff("1.0")


def test_to_string_includes_account_id():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    assert "0.0.5005" in str(query)


def test_should_retry_status_for_408():
    assert MirrorNodeAccountBalanceQuery._should_retry_status(408)


def test_should_retry_status_for_429():
    assert MirrorNodeAccountBalanceQuery._should_retry_status(429)


def test_should_retry_status_for_server_errors():
    assert MirrorNodeAccountBalanceQuery._should_retry_status(500)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(501)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(502)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(503)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(599)


def test_should_not_retry_status_for_success():
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(200)


def test_should_not_retry_status_for_client_errors():
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(400)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(401)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(403)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(404)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(422)


def test_should_not_retry_status_above_server_error_range():
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(600)


def test_to_account_id_param_uses_standard_account_id():
    account_id = AccountId.from_string("0.0.5005")

    result = MirrorNodeAccountBalanceQuery._to_account_id_param(account_id)

    assert result == "0.0.5005"
