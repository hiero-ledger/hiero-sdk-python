from __future__ import annotations

import base64
from unittest.mock import Mock, patch

import pytest
import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.mirror_node_token_balance import MirrorNodeTokenBalance
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.query.mirror_node_token_balance_query import MirrorNodeTokenBalanceQuery
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


def successful_response():
    """Return a successful mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "tokens": [
            {
                "token_id": "0.0.3",
                "balance": 100,
                "decimals": 2,
            }
        ]
    }
    return response


# __init__


# set_account_id


def test_set_account_id(mock_account_ids):
    """Test the setter method for account_id."""
    account_id = mock_account_ids[0]
    query = MirrorNodeTokenBalanceQuery()
    result = query.set_account_id(account_id)

    assert query.account_id == account_id
    assert result is not None
    assert result is query


@pytest.mark.parametrize("account_id", ["0.0.1", 100, 0.1, True, None, {}, []])
def test_set_invalid_account_id(account_id):
    """Test the setter method for account_id raise error for invalid account_id."""
    with pytest.raises(TypeError, match="account_id must be of type AccountId"):
        MirrorNodeTokenBalanceQuery().set_account_id(account_id)


# set_token_id


def test_set_token_id(token_id):
    """Test the setter method for token_id."""
    query = MirrorNodeTokenBalanceQuery()
    result = query.set_token_id(token_id)

    assert query.token_id == token_id
    assert result is not None
    assert result is query


@pytest.mark.parametrize("token_id", ["0.0.1", 100, 0.1, True, None, {}, []])
def test_set_invalid_token_id(token_id):
    """Test the setter method for token_id raise error for invalid token_id."""
    with pytest.raises(TypeError, match="token_id must be of type TokenId"):
        MirrorNodeTokenBalanceQuery().set_token_id(token_id)


# set_max_attempts


def test_set_max_attempts():
    """Test the setter method for max_attempts"""
    max_attempts = 5
    query = MirrorNodeTokenBalanceQuery()
    result = query.set_max_attempts(max_attempts)

    assert query.max_attempts == max_attempts
    assert result is not None
    assert result is query


@pytest.mark.parametrize("max_attempts", ["1", 0.1, True, None, {}, []])
def test_set_invalid_max_attempts(max_attempts):
    """Test the setter method for max_attempt raise error for invalid max_attempt type."""
    with pytest.raises(TypeError, match="max_attempts must be an integer"):
        MirrorNodeTokenBalanceQuery().set_max_attempts(max_attempts)


@pytest.mark.parametrize("max_attempts", [-1, 0])
def test_set_max_attempts_less_than_1(max_attempts):
    """Test the setter method for max_attempt raise error for attempt less than 1."""
    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        MirrorNodeTokenBalanceQuery().set_max_attempts(max_attempts)


# max_backoff


@pytest.mark.parametrize("max_backoff", [1, 1.5])
def test_set_max_backoff(max_backoff):
    """Test the setter method for max_backoff"""
    query = MirrorNodeTokenBalanceQuery()
    result = query.set_max_backoff(max_backoff)

    assert query.max_backoff == max_backoff
    assert result is not None
    assert result is query


@pytest.mark.parametrize("max_backoff", ["1", True, None, {}, []])
def test_set_invalid_max_backoff(max_backoff):
    """Test the setter method for max_backoff raise error for invalid max_backoff type."""
    with pytest.raises(TypeError, match="max_backoff must be a number"):
        MirrorNodeTokenBalanceQuery().set_max_backoff(max_backoff)


def test_set_max_backoff_less_than_threshold():
    """Test the setter method for max_backoff raise error for backoff less than 0.5."""
    with pytest.raises(ValueError, match="max_backoff must be at least 0.5 seconds"):
        MirrorNodeTokenBalanceQuery().set_max_backoff(0.4)


# _build_url


def test_build_url(mock_account_ids, token_id, mock_client):
    """Test build_url returns the proper URL string."""
    mock_base_url = "http://testnode/api/v1"
    mock_client.network.get_mirror_rest_url = Mock(return_value=mock_base_url)

    result = (
        MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)._build_url(mock_client)
    )

    expected_url = f"{mock_base_url}/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    assert result == expected_url


# _to_account_id_param


def test_account_params_from_account_id(mock_account_ids):
    """Test account params get resolve from the account_id."""
    account_id = mock_account_ids[0]
    result = MirrorNodeTokenBalanceQuery._to_account_id_param(account_id)

    assert result is not None
    assert result == str(account_id)


def test_account_params_from_account_id_having_evm_address():
    """Test account params get resolve from the account_id evm_address."""
    evm_address = PrivateKey.generate_ecdsa().public_key().to_evm_address()
    account_id = AccountId(0, 0, evm_address=evm_address)
    result = MirrorNodeTokenBalanceQuery._to_account_id_param(account_id)

    assert result is not None
    assert result == f"0x{str(evm_address)}"


def test_account_params_from_account_id_having_alias_key():
    """Test account params get resolve from the account_id alias_key."""
    alias_key = PrivateKey.generate_ecdsa().public_key()
    account_id = AccountId(0, 0, alias_key=alias_key)
    result = MirrorNodeTokenBalanceQuery._to_account_id_param(account_id)

    expected_alias = base64.b32encode(alias_key.to_proto_key().SerializeToString()).decode("ascii").rstrip("=")

    assert result is not None
    assert result == expected_alias


# _fetch_token_balance


def test_fetch_token_balance_success(mock_account_ids, token_id):
    """Test fetching token balance successfully."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    mock_response = successful_response()
    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get", return_value=mock_response
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
    ):
        result = query._fetch_token_balance(mock_url, timeout=10)

    assert result == mock_response.json.return_value
    mock_get.assert_called_once_with(mock_url, timeout=30)
    mock_delay.assert_not_called()


def test_fetch_token_balance_not_found(mock_account_ids, token_id):
    """Test fetching token balance with 404 status."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"status": "Not Found"}
    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get", return_value=mock_response
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
    ):
        result = query._fetch_token_balance(mock_url, timeout=10)

    assert result is None
    mock_get.assert_called_once_with(mock_url, timeout=30)
    mock_delay.assert_not_called()


@pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
def test_fetch_token_balance_with_retryable_status(status_code, mock_account_ids, token_id):
    """Test fetching token when get retryable status code."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    error_response = Mock()
    error_response.status_code = status_code
    error_response.text = "Error Response"

    response = successful_response()

    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            side_effect=[error_response, error_response, response],
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
    ):
        result = query._fetch_token_balance(mock_url, timeout=10)

    assert result == response.json.return_value
    assert mock_get.call_count == 3
    assert mock_delay.call_count == 2


@pytest.mark.parametrize("status_code", [408, 429, 500, 502, 503, 504])
def test_fetch_token_balance_fails_when_retries_reach_max_attempts(status_code, mock_account_ids, token_id):
    """Test fetching token when get retryable status code and max_attempt reach."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id).set_max_attempts(2)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    error_response = Mock()
    error_response.status_code = status_code
    error_response.text = "Error Response"

    response = successful_response()  # added so that we confirm no retry once reach max_attempt
    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            side_effect=[error_response, error_response, response],
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
        pytest.raises(MaxAttemptsError, match="Failed to fetch account balance after 2 attempts"),
    ):
        query._fetch_token_balance(mock_url, timeout=10)

    assert mock_get.call_count == 2
    assert mock_delay.call_count == 1


@pytest.mark.parametrize("status_code", [300, 400, 402, 505])
def test_fetch_token_balance_with_unretryable_status(status_code, mock_account_ids, token_id):
    """Test that non-retryable HTTP statuses raise an error without retrying."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    error_response = Mock()
    error_response.status_code = status_code
    error_response.text = "Error Response"

    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            return_value=error_response,
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
        pytest.raises(
            RuntimeError,
            match=f"Mirror node error: HTTP {status_code} - {error_response.text}",
        ),
    ):
        query._fetch_token_balance(mock_url, timeout=10)

    mock_get.assert_called_once_with(mock_url, timeout=30)
    mock_delay.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout("Request timed out"),
        requests.ConnectionError("Connection failed"),
    ],
)
def test_fetch_token_balance_with_retryable_network_errors(mock_account_ids, token_id, error):
    """Test raising RuntimeError when retryable networok error"""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    response = successful_response()

    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            side_effect=[error, error, response],
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
    ):
        result = query._fetch_token_balance(mock_url, timeout=10)

    assert result == response.json.return_value
    assert mock_get.call_count == 3
    assert mock_delay.call_count == 2


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout("Request timed out"),
        requests.ConnectionError("Connection failed"),
    ],
)
def test_fetch_token_balance_with_retryable_network_errors_when_retry_exausted(mock_account_ids, token_id, error):
    """Test raising RuntimeError when network retries are exhausted."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id).set_max_attempts(2)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    response = successful_response()  # added so that we confirm no retry once reach max_attempt

    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            side_effect=[error, error, response],
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
        pytest.raises(MaxAttemptsError, match="Failed to fetch MirrorNodeTokenBalance after 2 attempts"),
    ):
        query._fetch_token_balance(mock_url, timeout=10)

    assert mock_get.call_count == 2
    assert mock_delay.call_count == 1


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("Something went wrong"),
        ValueError("Something went wrong"),
    ],
)
def test_fetch_token_balance_with_unretryable_error(mock_account_ids, token_id, error):
    """Test raising RuntimeError when network retries are exhausted."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    with (
        patch(
            "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get",
            side_effect=[error],
        ) as mock_get,
        patch.object(query, "_delay_for_attempt") as mock_delay,
        pytest.raises(type(error), match=str(error)),
    ):
        query._fetch_token_balance(mock_url, timeout=10)

    assert mock_get.call_count == 1
    assert mock_delay.call_count == 0


# _delay_for_attempt


@pytest.mark.parametrize(
    ("attempt", "expected_delay"),
    [
        (1, 1),  # 0.5*2
        (2, 2),  # 0.5*4
        (3, 4),  # 0.5*8
        (4, 8),  # 0.5*16
    ],
)
def test_delay_for_attempt(attempt, expected_delay):
    """Test retry delay is properly calculated."""
    query = MirrorNodeTokenBalanceQuery()

    with patch("hiero_sdk_python.query.mirror_node_token_balance_query.time.sleep") as sleep:
        query._delay_for_attempt(attempt, Exception("Error"))
        sleep.assert_called_once_with(expected_delay)


def test_delay_for_attempt_cap_to_max_backoff():
    """Test retry delay is capped by max_backoff."""
    query = MirrorNodeTokenBalanceQuery()

    attempt = 5  # calculated backoff = 0.5 * 2^5 = 0.5 * 32 = 16
    expected = query.max_backoff  # 8 default
    with patch("hiero_sdk_python.query.mirror_node_token_balance_query.time.sleep") as sleep:
        query._delay_for_attempt(attempt, Exception("Error"))
        sleep.assert_called_once_with(expected)


# execute


@pytest.mark.parametrize("client", ["client", 1, True, [], {}])
def test_execute_with_invalid_client_type(client):
    """Test execute with invalid client type raise error."""
    with pytest.raises(TypeError, match="client must be of type Client"):
        MirrorNodeTokenBalanceQuery().execute(client)


def test_execute_with_none_client():
    """Test execute with client as none."""
    with pytest.raises(ValueError, match="client must not be None"):
        MirrorNodeTokenBalanceQuery().execute(None)


def test_execute_when_account_id_not_set(token_id, mock_client):
    """Test execute when account_id not set."""
    with pytest.raises(ValueError, match="account_id must be set before executing MirrorNodeTokenBalanceQuery"):
        MirrorNodeTokenBalanceQuery().set_token_id(token_id).execute(mock_client)


def test_execute_when_token_id_not_set(mock_account_ids, mock_client):
    """Test execute when token_id not set."""
    with pytest.raises(ValueError, match="token_id must be set before executing MirrorNodeTokenBalanceQuery"):
        MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).execute(mock_client)


def test_execute_with_valid_response(mock_account_ids, token_id, mock_client):
    """Test that execute parse the response to MirrorNodeTokenBalance."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)

    mock_base_url = "http://testnode/api/v1"
    mock_client.network.get_mirror_rest_url = Mock(return_value=mock_base_url)

    response = successful_response().json.return_value

    token = response["tokens"][0]
    expected_url = f"{mock_base_url}/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    # Without timeout
    with patch.object(query, "_fetch_token_balance", return_value=response) as mock_fetch:
        result = query.execute(mock_client)

    assert result == MirrorNodeTokenBalance(
        TokenId.from_string(token["token_id"]),
        token["balance"],
        token["decimals"],
    )
    mock_fetch.assert_called_once_with(expected_url, mock_client._request_timeout)

    # With timeout
    timeout = 10
    with patch.object(query, "_fetch_token_balance", return_value=response) as mock_fetch:
        result = query.execute(mock_client, timeout)

    assert result == MirrorNodeTokenBalance(
        TokenId.from_string(token["token_id"]),
        token["balance"],
        token["decimals"],
    )
    mock_fetch.assert_called_once_with(expected_url, timeout)


def test_execute_when_fetch_return_none(mock_account_ids, token_id, mock_client):
    """Test that execute parse the MirrorNodeTokenBalance when fetch return None"""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)

    mock_base_url = "http://testnode/api/v1"
    mock_client.network.get_mirror_rest_url = Mock(return_value=mock_base_url)

    expected_url = f"{mock_base_url}/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    # Without timeout
    with patch.object(query, "_fetch_token_balance", return_value=None) as mock_fetch:
        result = query.execute(mock_client)

    assert result == MirrorNodeTokenBalance(
        token_id,
        0,
        None,
    )
    mock_fetch.assert_called_once_with(expected_url, mock_client._request_timeout)

    # With timeout
    timeout = 10
    with patch.object(query, "_fetch_token_balance", return_value=None) as mock_fetch:
        result = query.execute(mock_client, timeout)

    assert result == MirrorNodeTokenBalance(
        token_id,
        0,
        None,
    )
    mock_fetch.assert_called_once_with(expected_url, timeout)


@pytest.mark.parametrize("response", ["response", {"tokens": "0.0.3"}, {"tokens": ["0.0.3"]}, object()])
def test_execute_raise_error_for_malformed_response(mock_account_ids, token_id, mock_client, response):
    """Test execute raise error for malformed response."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)

    mock_base_url = "http://testnode/api/v1"
    mock_client.network.get_mirror_rest_url = Mock(return_value=mock_base_url)

    with (
        patch.object(query, "_fetch_token_balance", return_value=response),
        pytest.raises(ValueError, match="Mirror Node returned a malformed JSON response"),
    ):
        query.execute(mock_client)
