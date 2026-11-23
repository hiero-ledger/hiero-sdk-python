from __future__ import annotations

import base64
import json
import re
from unittest.mock import Mock, patch

import pytest
import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MirrorNodeError
from hiero_sdk_python.query._mirror_node_rest import (
    mirror_node_error_from_response,
    send_with_retry,
    to_account_id_param,
    to_web3_rest_url,
)


pytestmark = pytest.mark.unit

EVM_HEX = "1234567890abcdef1234567890abcdef12345678"


def test_to_account_id_param_plain_account_id():
    """A plain shard.realm.num account ID is sent unchanged."""
    account_id = AccountId(0, 0, 1234)

    assert to_account_id_param(account_id) == "0.0.1234"


def test_to_account_id_param_evm_address_object():
    """An EvmAddress object is sent as 0x-prefixed lowercase hex."""
    account_id = AccountId(0, 0, 0, evm_address=EvmAddress.from_string("0x" + EVM_HEX))

    result = to_account_id_param(account_id)

    assert result == "0x" + EVM_HEX
    assert re.fullmatch(r"0x[0-9a-f]{40}", result)


def test_to_account_id_param_evm_address_raw_bytes():
    """An EVM address held as raw 20 bytes is sent as 0x-prefixed hex."""
    raw = bytes.fromhex(EVM_HEX)
    account_id = AccountId(0, 0, 0, evm_address=EvmAddress.from_bytes(raw))
    account_id.evm_address = raw  # exercise the raw-bytes branch directly

    result = to_account_id_param(account_id)

    assert result == "0x" + raw.hex()


def test_to_account_id_param_public_key_alias():
    """A public key alias is sent as unpadded base32 of its protobuf key bytes."""
    alias_key = PrivateKey.generate_ed25519().public_key()
    account_id = AccountId(0, 0, 0, alias_key=alias_key)

    result = to_account_id_param(account_id)

    expected_bytes = alias_key.to_proto_key().SerializeToString()
    expected = base64.b32encode(expected_bytes).decode("ascii").rstrip("=")

    assert result == expected
    assert "=" not in result


# to_web3_rest_url


@pytest.mark.parametrize(
    ("rest_url", "expected"),
    [
        ("http://localhost:38081/api/v1", "http://localhost:8545/api/v1"),
        ("http://127.0.0.1:38081/api/v1", "http://127.0.0.1:8545/api/v1"),
        ("http://localhost:5551/api/v1", "http://localhost:5551/api/v1"),
        ("https://testnet.mirrornode.hedera.com/api/v1", "https://testnet.mirrornode.hedera.com/api/v1"),
    ],
)
def test_to_web3_rest_url(rest_url, expected):
    """Only a local mirror node on port 38081 is redirected to the web3 port."""
    assert to_web3_rest_url(rest_url) == expected


# send_with_retry

_REQUEST = "hiero_sdk_python.query._mirror_node_rest.requests.request"
_SLEEP = "hiero_sdk_python.query._mirror_node_rest.time.sleep"
_MONOTONIC = "hiero_sdk_python.query._mirror_node_rest.time.monotonic"


def _response(status_code, body=None):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = body
    return resp


def _send(**overrides):
    kwargs = {
        "timeout": 10,
        "max_attempts": 3,
        "max_backoff": 8,
        "retryable_statuses": {503},
    }
    kwargs.update(overrides)
    return send_with_retry("GET", "http://mirror/api/v1/x", **kwargs)


def test_send_with_retry_get_has_no_body():
    """A request without a JSON body sends no data and no Content-Type."""
    with patch(_REQUEST, return_value=_response(200)) as mock_request:
        _send()

    kwargs = mock_request.call_args.kwargs
    assert kwargs["data"] is None
    assert "Content-Type" not in kwargs["headers"]
    assert kwargs["headers"]["Accept"] == "application/json"


def test_send_with_retry_post_serializes_json_body():
    """A JSON body is serialized and sent as application/json."""
    with patch(_REQUEST, return_value=_response(200)) as mock_request:
        send_with_retry(
            "POST",
            "http://mirror/api/v1/x",
            timeout=10,
            max_attempts=1,
            max_backoff=8,
            retryable_statuses=set(),
            json_body={"a": 1},
        )

    kwargs = mock_request.call_args.kwargs
    assert mock_request.call_args.args == ("POST", "http://mirror/api/v1/x")
    assert json.loads(kwargs["data"]) == {"a": 1}
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_send_with_retry_returns_non_retryable_response_immediately():
    """A non-retryable error status is returned to the caller without retrying."""
    with patch(_REQUEST, return_value=_response(400)) as mock_request, patch(_SLEEP) as mock_sleep:
        result = _send()

    assert result.status_code == 400
    assert mock_request.call_count == 1
    mock_sleep.assert_not_called()


def test_send_with_retry_returns_last_retryable_response_when_exhausted():
    """When every attempt returns a retryable status, the last response is returned."""
    with patch(_REQUEST, return_value=_response(503)) as mock_request, patch(_SLEEP) as mock_sleep:
        result = _send()

    assert result.status_code == 503
    assert mock_request.call_count == 3
    assert mock_sleep.call_count == 2


def test_send_with_retry_backoff_is_capped():
    """The delay grows exponentially but never exceeds max_backoff."""
    with patch(_REQUEST, return_value=_response(503)), patch(_SLEEP) as mock_sleep:
        _send(max_attempts=5, max_backoff=3, timeout=1000)

    delays = [call.args[0] for call in mock_sleep.call_args_list]
    assert delays == [1.0, 2.0, 3, 3]


def test_send_with_retry_transport_error_after_retryable_status_raises():
    """A transport failure on the last attempt raises even if an earlier attempt got a response."""
    with (
        patch(_REQUEST, side_effect=[_response(503), requests.ConnectionError("down")]),
        patch(_SLEEP),
        pytest.raises(RuntimeError, match="after 2 attempts"),
    ):
        _send(max_attempts=2)


def test_send_with_retry_deadline_exceeded_after_transport_error_raises():
    """The total deadline stops further attempts; with no response to return, it raises."""
    # start, attempt 1 check, delay cap, attempt 2 check (past the deadline)
    with (
        patch(_MONOTONIC, side_effect=[0.0, 0.0, 1.0, 11.0]),
        patch(_REQUEST, side_effect=requests.ConnectionError("down")) as mock_request,
        patch(_SLEEP),
        pytest.raises(RuntimeError, match="total timeout of 10s exceeded") as exc_info,
    ):
        _send(max_attempts=5, timeout=10)

    assert mock_request.call_count == 1
    assert isinstance(exc_info.value.__cause__, requests.ConnectionError)


def test_send_with_retry_deadline_exceeded_returns_last_retryable_response():
    """When the deadline stops a retry after a retryable status, that response is returned."""
    # start, attempt 1 check, delay cap, attempt 2 check (past the deadline)
    with (
        patch(_MONOTONIC, side_effect=[0.0, 0.0, 1.0, 11.0]),
        patch(_REQUEST, return_value=_response(429)) as mock_request,
        patch(_SLEEP),
    ):
        result = _send(max_attempts=5, timeout=10, retryable_statuses={429})

    assert result.status_code == 429
    assert mock_request.call_count == 1


# mirror_node_error_from_response


def test_error_from_response_collects_every_message():
    """Every _status.messages entry is kept, with detail and data when present."""
    body = {
        "_status": {
            "messages": [
                {"message": "CONTRACT_REVERT_EXECUTED", "detail": "Not allowed", "data": "0x08c379a0"},
                {"message": "Second"},
                "not a dict",
                {"detail": ""},
            ]
        }
    }

    error = mirror_node_error_from_response(_response(400, body))

    assert isinstance(error, MirrorNodeError)
    assert error.status_code == 400
    assert error.messages == ["CONTRACT_REVERT_EXECUTED: Not allowed", "Second"]
    assert error.data == ["0x08c379a0"]
    assert str(error) == "Mirror node returned HTTP 400: CONTRACT_REVERT_EXECUTED: Not allowed; Second"


@pytest.mark.parametrize("body", [None, {}, {"_status": {}}, {"_status": {"messages": []}}, []])
def test_error_from_response_falls_back_to_reason_phrase(body):
    """Without _status.messages the HTTP reason phrase is used."""
    error = mirror_node_error_from_response(_response(429, body))

    assert error.messages == ["Too Many Requests"]
    assert str(error) == "Mirror node returned HTTP 429: Too Many Requests"


def test_error_from_response_with_unknown_status_and_no_body():
    """An unknown status code with no body still produces an error."""
    resp = _response(599)
    resp.json.side_effect = ValueError("no json")

    error = mirror_node_error_from_response(resp)

    assert error.messages == []
    assert str(error) == "Mirror node returned HTTP 599"
