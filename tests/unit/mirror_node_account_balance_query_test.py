"""
Unit tests for MirrorNodeAccountBalanceQuery.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from hiero_sdk_python import AccountId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query.mirror_node_account_balance_query import (
    MirrorNodeAccountBalanceQuery,
)


def test_constructor_sets_account_id_and_defaults():
    """Test that the constructor sets the account ID and default values."""
    account_id = AccountId.from_string("0.0.5005")

    query = MirrorNodeAccountBalanceQuery(account_id)

    assert query.account_id == account_id
    assert query.max_attempts == 10
    assert query.max_backoff == 8.0


def test_setters_are_fluent_and_round_trip():
    """Test that setter methods update values and return the query instance."""
    initial_account_id = AccountId.from_string("0.0.5005")
    updated_account_id = AccountId.from_string("0.0.6006")

    query = (
        MirrorNodeAccountBalanceQuery(initial_account_id)
        .set_account_id(updated_account_id)
        .set_max_attempts(3)
        .set_max_backoff(0.5)
    )

    assert query.account_id == updated_account_id
    assert query.max_attempts == 3
    assert query.max_backoff == 0.5


def test_constructor_allows_none_account_id():
    """Test that the constructor allows an unset account ID."""
    query = MirrorNodeAccountBalanceQuery()

    assert query.account_id is None


def test_set_account_id_rejects_none():
    """Test that set_account_id raises an error when given None."""
    with pytest.raises(ValueError, match="account_id must not be None"):
        MirrorNodeAccountBalanceQuery().set_account_id(None)


@pytest.mark.parametrize("account_id", ["0.0.1", True, 1, 0.2, {}, []])
def test_set_account_id_rejects_invalid_type(account_id):
    """Test that set_account_id rejects values that are not AccountId instances."""
    with pytest.raises(TypeError, match="account_id must be an AccountId instance"):
        MirrorNodeAccountBalanceQuery().set_account_id(account_id)


@pytest.mark.parametrize("attempts", [-1, 0])
def test_set_max_attempts_rejects_attempt_less_than_one(attempts):
    """Test that set_max_attempts rejects values less than one."""
    with pytest.raises(ValueError, match="greater than zero"):
        MirrorNodeAccountBalanceQuery().set_max_attempts(attempts)


@pytest.mark.parametrize("attempts", ["1", True, None, 0.2, {}, []])
def test_set_max_attempts_rejects_non_integer(attempts):
    """Test that set_max_attempts rejects non-integer values."""

    with pytest.raises(TypeError, match="max_attempts must be an integer"):
        MirrorNodeAccountBalanceQuery().set_max_attempts(attempts)


def test_set_max_backoff_rejects_values_below_half_second():
    """Test that set_max_backoff rejects values below 0.5 seconds."""
    with pytest.raises(ValueError, match="at least 0.5 seconds"):
        MirrorNodeAccountBalanceQuery().set_max_backoff(0.499)


@pytest.mark.parametrize("backoff", ["1", True, None, {}, []])
def test_set_max_backoff_rejects_non_numeric(backoff):
    """Test that set_max_backoff rejects non-numeric values."""
    with pytest.raises(
        TypeError,
        match="max_backoff must be a number",
    ):
        MirrorNodeAccountBalanceQuery().set_max_backoff(backoff)


def test_to_string_includes_account_id():
    """Test that the string representation includes the account ID."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))
    assert "0.0.5005" in str(query)


def test_should_retry_status_for_408():
    """Test that HTTP 408 is considered retryable."""
    assert MirrorNodeAccountBalanceQuery._should_retry_status(408)


def test_should_retry_status_for_429():
    """Test that HTTP 429 is considered retryable."""
    assert MirrorNodeAccountBalanceQuery._should_retry_status(429)


def test_should_retry_status_for_server_errors():
    """Test that HTTP 5xx status codes are considered retryable."""
    assert MirrorNodeAccountBalanceQuery._should_retry_status(500)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(501)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(502)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(503)
    assert MirrorNodeAccountBalanceQuery._should_retry_status(599)


def test_should_not_retry_status_for_success():
    """Test that HTTP 200 is not considered retryable."""
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(200)


def test_should_not_retry_status_for_client_errors():
    """Test that non-retryable HTTP 4xx status codes are not retried."""
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(400)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(401)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(403)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(404)
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(422)


def test_should_not_retry_status_above_server_error_range():
    """Test that HTTP status codes above 599 are not considered retryable."""
    assert not MirrorNodeAccountBalanceQuery._should_retry_status(600)


def test_to_account_id_param_uses_standard_account_id():
    """Test that an account ID without an alias uses its standard string format."""
    account_id = AccountId.from_string("0.0.5005")

    result = MirrorNodeAccountBalanceQuery._to_account_id_param(account_id)

    assert result == "0.0.5005"


def test_execute_rejects_none_client():
    """Test that execute raises an error when the client is None."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        query.execute(None)


def test_execute_uses_client_request_timeout_when_timeout_is_none():
    """Test that execute uses the client's request timeout when no timeout is provided."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()
    client._request_timeout = 15.0

    expected_balance = MagicMock()

    with (
        patch.object(
            query,
            "_build_url",
            return_value="https://example.com/balances",
        ),
        patch.object(
            query,
            "_fetch_body",
            return_value={"balances": []},
        ) as fetch_body,
        patch(
            "hiero_sdk_python.query.mirror_node_account_balance_query.MirrorNodeAccountBalance",
        ) as balance_class,
    ):
        balance_class._from_json.return_value = expected_balance

        result = query.execute(client, timeout=None)

    assert result is expected_balance
    fetch_body.assert_called_once_with(
        "https://example.com/balances",
        15.0,
    )
    balance_class._from_json.assert_called_once_with({"balances": []})


def test_execute_uses_default_timeout_when_client_has_no_request_timeout():
    """Test that execute uses the default timeout when the client has no request timeout."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock(spec=["network"])
    expected_balance = MagicMock()

    with (
        patch.object(
            query,
            "_build_url",
            return_value="https://example.com/balances",
        ),
        patch.object(
            query,
            "_fetch_body",
            return_value={"balances": []},
        ) as fetch_body,
        patch(
            "hiero_sdk_python.query.mirror_node_account_balance_query.MirrorNodeAccountBalance",
        ) as balance_class,
    ):
        balance_class._from_json.return_value = expected_balance

        result = query.execute(client, timeout=None)

    assert result is expected_balance
    fetch_body.assert_called_once_with(
        "https://example.com/balances",
        30.0,
    )
    balance_class._from_json.assert_called_once_with({"balances": []})


def test_execute_raises_precheck_error_when_balance_is_none():
    """Test that execute raises a PrecheckError when no account balance is returned."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()

    with (
        patch.object(
            query,
            "_build_url",
            return_value="https://example.com/balances",
        ),
        patch.object(
            query,
            "_fetch_body",
            return_value={"balances": []},
        ),
        patch(
            "hiero_sdk_python.query.mirror_node_account_balance_query.MirrorNodeAccountBalance",
        ) as balance_class,
        pytest.raises(
            PrecheckError,
            match="INVALID_ACCOUNT_ID",
        ),
    ):
        balance_class._from_json.return_value = None

        query.execute(client)


def test_build_url():
    """Test that _build_url creates the expected mirror node REST URL."""
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
    """Test that _fetch_body retries requests for retryable HTTP status codes."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(2)

    first_response = MagicMock()
    first_response.status_code = status_code

    second_response = MagicMock()
    second_response.status_code = 200
    second_response.read.return_value = json.dumps(
        {
            "balances": [
                {
                    "balance": 100,
                }
            ]
        }
    ).encode("utf-8")

    with (
        patch.object(
            query,
            "_request",
            side_effect=[
                (status_code, first_response, None),
                (200, second_response, None),
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
    """Test that _fetch_body does not retry non-retryable HTTP status codes."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(3)

    response = MagicMock()
    response.status_code = 404

    with (
        patch.object(
            query,
            "_request",
            return_value=(404, response, None),
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
    """Test that _fetch_body stops retrying after the configured maximum attempts."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005")).set_max_attempts(3)

    response = MagicMock()
    response.status_code = 503

    with (
        patch.object(
            query,
            "_request",
            return_value=(503, response, None),
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
    """Test that _request returns the response for a successful request."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    response = MagicMock()
    response.status = 200

    with patch(
        "hiero_sdk_python.query.mirror_node_account_balance_query.urlopen",
        return_value=response,
    ) as urlopen:
        status_code, result, error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert status_code == 200
    assert error is None
    assert result is response

    urlopen.assert_called_once()


def test_request_returns_http_error_status_without_exception():
    """Test that _request returns the HTTP error status without an exception."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

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
        status_code, result, request_error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert status_code == 429
    assert result is None
    assert request_error is None


def test_request_returns_exception_for_url_error():
    """Test that _to_account_id_param uses the EVM address when provided as bytes."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    error = URLError("connection failed")

    with patch(
        "hiero_sdk_python.query.mirror_node_account_balance_query.urlopen",
        side_effect=error,
    ):
        status_code, result, request_error = query._request(
            "https://example.com/balances",
            30.0,
        )

    assert status_code == 0
    assert result is None
    assert request_error is error


def test_to_account_id_param_uses_evm_address_bytes():
    """Test that _to_account_id_param uses the EVM address when provided as bytes."""
    account_id = MagicMock(spec=AccountId)
    account_id.evm_address = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")
    account_id.alias_key = None

    result = MirrorNodeAccountBalanceQuery._to_account_id_param(account_id)

    assert result == "0x1234567890abcdef1234567890abcdef12345678"


def test_to_account_id_param_uses_evm_address_string():
    """Test that _to_account_id_param uses the EVM address when provided as a string."""
    account_id = MagicMock(spec=AccountId)
    account_id.evm_address = "1234567890abcdef1234567890abcdef12345678"
    account_id.alias_key = None

    result = MirrorNodeAccountBalanceQuery._to_account_id_param(account_id)

    assert result == "0x1234567890abcdef1234567890abcdef12345678"


def test_to_account_id_param_uses_public_key_alias():
    """Test that _to_account_id_param uses the public key alias when no EVM address is available."""
    account_id = MagicMock(spec=AccountId)
    account_id.evm_address = None

    alias_key = MagicMock()
    protobuf_key = MagicMock()
    protobuf_key.SerializeToString.return_value = b"test-key-bytes"
    alias_key.to_proto_key.return_value = protobuf_key

    account_id.alias_key = alias_key

    result = MirrorNodeAccountBalanceQuery._to_account_id_param(account_id)

    expected = base64.b32encode(b"test-key-bytes").decode("ascii").rstrip("=")

    assert result == expected
    alias_key.to_proto_key.assert_called_once()
    protobuf_key.SerializeToString.assert_called_once()


def test_constructor_init_with_invalid_account_id_type():
    """Test that the constructor rejects an invalid account ID type."""
    with pytest.raises(
        TypeError,
        match="account_id must be an AccountId",
    ):
        MirrorNodeAccountBalanceQuery(account_id="0.0.5005")


def test_execute_raises_error_when_malformed_json_is_received():
    """Test that execute raises an error when the mirror node returns malformed JSON."""
    query = MirrorNodeAccountBalanceQuery(AccountId.from_string("0.0.5005"))

    client = MagicMock()

    with (
        patch.object(
            query,
            "_build_url",
            return_value="https://example.com/balances",
        ),
        patch.object(
            query,
            "_fetch_body",
            return_value={"not balances": []},
        ),
        pytest.raises(
            ValueError,
            match="Mirror Node returned a malformed JSON response",
        ),
    ):
        query.execute(client)


def test_execute_raise_error_if_no_account_id_set(mock_client):
    """Test that execute raises an error when no account ID is set."""
    with pytest.raises(ValueError, match="accountId must be set before executing MirrorNodeAccountBalanceQuery"):
        MirrorNodeAccountBalanceQuery().execute(mock_client)
