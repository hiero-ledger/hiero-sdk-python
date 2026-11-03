"""Adapter-level tests for the getMirrorNodeTokenBalance TCK JSON-RPC method."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from hiero_sdk_python import AccountId, Client, PrivateKey
from hiero_sdk_python.account.mirror_node_token_balance import MirrorNodeTokenBalance
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query.mirror_node_token_balance_query import MirrorNodeTokenBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from tck.errors import HIERO_ERROR, INTERNAL_ERROR, INVALID_PARAMS, JsonRpcError
from tck.handlers import account, registry
from tck.handlers.registry import dispatch, get_all_handlers, get_handler, rpc_method
from tck.param.account import GetMirrorNodeTokenBalanceParams


pytestmark = pytest.mark.unit

_REGISTERED_HANDLERS = get_all_handlers()


@pytest.fixture(autouse=True)
def restore_account_handlers():
    """Preserve account handler registration across registry-clearing fixtures."""
    registry._HANDLERS.update(_REGISTERED_HANDLERS)
    rpc_method("getMirrorNodeTokenBalance")(account.get_mirror_node_token_balance)


def test_get_mirror_node_token_balance_is_registered():
    handler = get_handler("getMirrorNodeTokenBalance")
    assert handler is not None
    assert getattr(handler, "__wrapped__", None) is account.get_mirror_node_token_balance


def test_params_parse_optional_identifiers_and_require_session():
    params = GetMirrorNodeTokenBalanceParams.parse_json_params(
        {"sessionId": "s", "accountId": "0.0.100", "tokenId": "0.0.200"}
    )
    assert params.sessionId == "s"
    assert params.accountId == "0.0.100"
    assert params.tokenId == "0.0.200"
    assert not hasattr(params, "commonTransactionParams")

    empty_params = GetMirrorNodeTokenBalanceParams.parse_json_params({"sessionId": "s"})
    assert empty_params.accountId is None
    assert empty_params.tokenId is None


@pytest.mark.parametrize(
    ("balance_result", "expected_response"),
    [
        (
            MirrorNodeTokenBalance(TokenId(0, 0, 200), 250, 2, associated=True),
            {"tokenId": "0.0.200", "balance": "250", "decimals": 2},
        ),
        (
            MirrorNodeTokenBalance(TokenId(0, 0, 201), 3, 0, associated=True),
            {"tokenId": "0.0.201", "balance": "3", "decimals": 0},
        ),
        (
            MirrorNodeTokenBalance(TokenId(0, 0, 202), 0, 6, associated=True),
            {"tokenId": "0.0.202", "balance": "0", "decimals": 6},
        ),
        (
            MirrorNodeTokenBalance(TokenId(0, 0, 203), 0, 0, associated=False),
            {"tokenId": "0.0.203", "balance": "0", "decimals": 0},
        ),
        (
            MirrorNodeTokenBalance(TokenId(0, 0, 204), 9007199254740993, 8, associated=True),
            {"tokenId": "0.0.204", "balance": "9007199254740993", "decimals": 8},
        ),
    ],
)
def test_dispatch_serializes_mirror_node_token_balance_responses(balance_result, expected_response):
    client = Mock()
    query = MagicMock(spec=MirrorNodeTokenBalanceQuery)
    query.execute.return_value = balance_result

    with (
        patch("tck.handlers.account.get_client", return_value=client) as mock_get_client,
        patch("tck.handlers.account.MirrorNodeTokenBalanceQuery", return_value=query),
    ):
        result = dispatch(
            "getMirrorNodeTokenBalance",
            {
                "sessionId": "s",
                "accountId": "0.0.100",
                "tokenId": str(balance_result.token_id),
            },
        )

    mock_get_client.assert_called_once_with("s")
    query.set_account_id.assert_called_once_with(AccountId.from_string("0.0.100"))
    query.set_token_id.assert_called_once_with(balance_result.token_id)
    query.execute.assert_called_once_with(client)
    assert result == expected_response


@pytest.mark.parametrize(
    "account_id_str",
    [
        "0.0.100",
        "0x0000000000000000000000000000000000000064",
        "0000000000000000000000000000000000000064",
        f"0.0.{PrivateKey.generate_ed25519().public_key().to_string_der()}",
    ],
)
def test_setters_receive_parsed_account_id_and_token_id(account_id_str):
    client = Mock()
    query = MagicMock(spec=MirrorNodeTokenBalanceQuery)
    query.execute.return_value = MirrorNodeTokenBalance(TokenId(0, 0, 200), 250, 2, associated=True)

    with (
        patch("tck.handlers.account.get_client", return_value=client),
        patch("tck.handlers.account.MirrorNodeTokenBalanceQuery", return_value=query),
    ):
        result = dispatch(
            "getMirrorNodeTokenBalance",
            {
                "sessionId": "s",
                "accountId": account_id_str,
                "tokenId": "0.0.200",
            },
        )

    query.set_account_id.assert_called_once_with(AccountId.from_string(account_id_str))
    query.set_token_id.assert_called_once_with(TokenId.from_string("0.0.200"))
    query.execute.assert_called_once_with(client)
    assert result == {"tokenId": "0.0.200", "balance": "250", "decimals": 2}


def test_precheck_invalid_account_id_maps_to_hiero_error_with_status():
    client = Mock()
    query = MagicMock(spec=MirrorNodeTokenBalanceQuery)
    query.execute.side_effect = PrecheckError(ResponseCode.INVALID_ACCOUNT_ID)

    with (
        patch("tck.handlers.account.get_client", return_value=client),
        patch("tck.handlers.account.MirrorNodeTokenBalanceQuery", return_value=query),
        pytest.raises(JsonRpcError) as error,
    ):
        dispatch(
            "getMirrorNodeTokenBalance",
            {"sessionId": "s", "accountId": "0.0.100", "tokenId": "0.0.200"},
        )

    assert error.value.code == HIERO_ERROR
    assert error.value.data == {"status": "INVALID_ACCOUNT_ID"}


@pytest.mark.parametrize(
    "params",
    [
        {"sessionId": "s", "tokenId": "0.0.200"},
        {"sessionId": "s", "accountId": "0.0.100"},
        {"sessionId": "s"},
    ],
)
def test_missing_identifiers_use_real_sdk_query_and_never_fetch(params):
    with (
        Client.for_network({"localhost:50211": AccountId(0, 0, 3)}) as client,
        patch("tck.handlers.account.get_client", return_value=client),
        patch.object(MirrorNodeTokenBalanceQuery, "_fetch_token_balance") as mock_fetch,
        patch("hiero_sdk_python.query.mirror_node_token_balance_query.requests.get") as mock_get,
        pytest.raises(JsonRpcError) as error,
    ):
        dispatch("getMirrorNodeTokenBalance", params)

    assert error.value.code == INTERNAL_ERROR
    assert isinstance(error.value.__cause__, ValueError)
    mock_fetch.assert_not_called()
    mock_get.assert_not_called()


@pytest.mark.parametrize("bad_account_id", ["", " ", "malformed", "0.0.x", 100])
def test_malformed_account_id_maps_to_internal_error_without_executing(bad_account_id):
    client = Mock()
    query = MagicMock(spec=MirrorNodeTokenBalanceQuery)

    with (
        patch("tck.handlers.account.get_client", return_value=client),
        patch("tck.handlers.account.MirrorNodeTokenBalanceQuery", return_value=query),
        pytest.raises(JsonRpcError) as error,
    ):
        dispatch(
            "getMirrorNodeTokenBalance",
            {"sessionId": "s", "accountId": bad_account_id, "tokenId": "0.0.200"},
        )

    assert error.value.code == INTERNAL_ERROR
    assert isinstance(error.value.__cause__, (TypeError, ValueError))
    query.execute.assert_not_called()


@pytest.mark.parametrize("bad_token_id", ["", " ", "malformed", "0.0.x", 200])
def test_malformed_token_id_maps_to_internal_error_without_executing(bad_token_id):
    client = Mock()
    query = MagicMock(spec=MirrorNodeTokenBalanceQuery)

    with (
        patch("tck.handlers.account.get_client", return_value=client),
        patch("tck.handlers.account.MirrorNodeTokenBalanceQuery", return_value=query),
        pytest.raises(JsonRpcError) as error,
    ):
        dispatch(
            "getMirrorNodeTokenBalance",
            {"sessionId": "s", "accountId": "0.0.100", "tokenId": bad_token_id},
        )

    assert error.value.code == INTERNAL_ERROR
    assert isinstance(error.value.__cause__, (TypeError, ValueError))
    query.execute.assert_not_called()


def test_missing_session_id_maps_to_invalid_params():
    with pytest.raises(JsonRpcError) as error:
        dispatch("getMirrorNodeTokenBalance", {"accountId": "0.0.100", "tokenId": "0.0.200"})

    assert error.value.code == INVALID_PARAMS
