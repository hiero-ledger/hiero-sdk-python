"""
Unit tests for MirrorNodeAccountBalanceQuery.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python import AccountId
from hiero_sdk_python.exceptions import PrecheckError
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
        match="max_backoff must be a number",
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


def test_execute_rejects_none_client():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        query.execute(None)


def test_execute_uses_client_request_timeout_when_timeout_is_none():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()
    client.request_timeout = 15.0

    expected_balance = MagicMock()

    with (
        patch.object(query, "_build_url", return_value="https://example.com/balances"),
        patch.object(query, "_fetch_body", return_value={"balances": []}) as fetch_body,
        patch(
            "hiero_sdk_python.query.mirror_node_account_balance_query.MirrorNodeAccountBalance.from_json",
            return_value=expected_balance,
        ),
    ):
        result = query.execute(client, timeout=None)

    assert result is expected_balance
    fetch_body.assert_called_once_with(
        "https://example.com/balances",
        15.0,
    )


def test_execute_uses_default_timeout_when_client_has_no_request_timeout():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock(spec=["network"])

    expected_balance = MagicMock()

    with (
        patch.object(query, "_build_url", return_value="https://example.com/balances"),
        patch.object(query, "_fetch_body", return_value={"balances": []}) as fetch_body,
        patch(
            "hiero_sdk_python.query.mirror_node_account_balance_query.MirrorNodeAccountBalance.from_json",
            return_value=expected_balance,
        ),
    ):
        result = query.execute(client, timeout=None)

    assert result is expected_balance
    fetch_body.assert_called_once_with(
        "https://example.com/balances",
        30.0,
    )


def test_execute_raises_precheck_error_when_balance_is_none():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()

    with (
        patch.object(query, "_build_url", return_value="https://example.com/balances"),
        patch.object(
            query,
            "_fetch_body",
            return_value={"balances": []},
        ),
        pytest.raises(
            PrecheckError,
            match="INVALID_ACCOUNT_ID",
        ),
    ):
        query.execute(client)


def test_build_url():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()
    client.network.get_mirror_rest_url.return_value = "https://testnet.mirrornode.hedera.com/"

    result = query._build_url(client)

    assert result == ("https://testnet.mirrornode.hedera.com/balances?account.id=0.0.5005")


@pytest.mark.parametrize(
    "status_code",
    [408, 429, 500, 501, 502, 503, 599],
)
def test_fetch_body_retries_retryable_http_statuses(status_code):
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(2)

    first_response = MagicMock()
    first_response.status_code = status_code

    second_response = MagicMock()
    second_response.status_code = 200
    second_response.json.return_value = {
        "balances": [
            {
                "balance": 100,
            }
        ]
    }

    with (
        patch.object(
            query,
            "_request",
            side_effect=[
                (first_response, None),
                (second_response, None),
            ],
        ) as request,
        patch.object(query, "_warn_and_delay") as warn_and_delay,
    ):
        result = query._fetch_body(
            "https://example.com/balances",
            30.0,
        )

    assert result == {
        "balances": [
            {
                "balance": 100,
            }
        ]
    }
    assert request.call_count == 2
    warn_and_delay.assert_called_once()


def test_fetch_body_does_not_retry_non_retryable_http_status():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(3)

    response = MagicMock()
    response.status_code = 404

    with (
        patch.object(
            query,
            "_request",
            return_value=(response, None),
        ) as request,
        patch.object(query, "_warn_and_delay") as warn_and_delay,
        pytest.raises(
            RuntimeError,
            match="Mirror Node error: HTTP 404",
        ),
    ):
        query._fetch_body(
            "https://example.com/balances",
            30.0,
        )

    request.assert_called_once()
    warn_and_delay.assert_not_called()


def test_fetch_body_stops_retrying_after_max_attempts():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(3)

    response = MagicMock()
    response.status_code = 503

    with (
        patch.object(
            query,
            "_request",
            return_value=(response, None),
        ) as request,
        patch.object(query, "_warn_and_delay") as warn_and_delay,
        pytest.raises(
            RuntimeError,
            match="Mirror Node error: HTTP 503",
        ),
    ):
        query._fetch_body(
            "https://example.com/balances",
            30.0,
        )

    assert request.call_count == 3
    assert warn_and_delay.call_count == 2


def test_request_returns_response_for_success():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    response = MagicMock()
    response.status = 200

    with patch(
        "hiero_sdk_python.query.mirror_node_account_balance_query.urlopen",
        return_value=response,
    ) as urlopen:
        result, error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert error is None
    assert result.status_code == 200

    urlopen.assert_called_once()


def test_request_returns_http_error_status_without_exception():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    from urllib.error import HTTPError

    error = HTTPError(
        "https://example.com/balances",
        429,
        "Too Many Requests",
        None,
        None,
    )

    with patch(
        "hiero_sdk_python.query.mirror_node_account_balance_query.urlopen",
        side_effect=error,
    ):
        result, request_error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert request_error is None
    assert result.status_code == 429


def test_request_returns_exception_for_url_error():
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    from urllib.error import URLError

    error = URLError("connection failed")

    with patch(
        "hiero_sdk_python.query.mirror_node_account_balance_query.urlopen",
        side_effect=error,
    ):
        result, request_error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert result is None
    assert request_error is error
