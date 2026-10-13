from __future__ import annotations

import base64
from unittest.mock import Mock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query.mirror_node_token_balance_query import MirrorNodeTokenBalanceQuery


pytestmark = pytest.mark.unit


@pytest.fixture
def successful_response():
    """Return a successful mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "tokens": [
            {
                "token_id": "0.0.5678",
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


def test_fetch_token_balance_success(mock_account_ids, token_id, successful_response):
    """Test fetching token balance successfully."""
    query = MirrorNodeTokenBalanceQuery().set_account_id(mock_account_ids[0]).set_token_id(token_id)
    mock_url = f"http://testnode/api/v1/accounts/{mock_account_ids[0]}/tokens?token.id={token_id}&limit=1"

    with patch(
        "hiero_sdk_python.query.mirror_node_token_balance_query.requests.get", return_value=successful_response
    ) as mock_get:
        result = query._fetch_token_balance(mock_url, timeout=10)

    assert result == successful_response.json.return_value
    mock_get.assert_called_once_with(mock_url, timeout=30)
