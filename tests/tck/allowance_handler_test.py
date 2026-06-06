"""Tests for the TCK allowance handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.response_code import ResponseCode
from tck.errors import INTERNAL_ERROR, INVALID_PARAMS
from tck.handlers.allowance import _build_delete_allowance_transaction, delete_allowance
from tck.handlers.registry import safe_dispatch
from tck.param.allowance import DeleteAllowanceParams


pytestmark = pytest.mark.unit


def _params(allowances):
    return DeleteAllowanceParams.parse_json_params(
        {
            "sessionId": "allowance-test",
            "allowances": allowances,
        }
    )


def test_parse_delete_allowance_flat_and_nested_formats():
    flat = _params(
        [
            {
                "ownerAccountId": "0.0.1001",
                "tokenId": "0.0.2001",
                "serialNumbers": ["1", "2"],
            }
        ]
    )
    nested = _params(
        [
            {
                "ownerAccountId": "0.0.1001",
                "nft": {
                    "tokenId": "0.0.2001",
                    "serialNumbers": ["1", "2"],
                },
            }
        ]
    )

    assert flat.allowances == nested.allowances


@pytest.mark.parametrize("unsupported_field", ["hbar", "token"])
def test_delete_allowance_rejects_non_nft_allowances(unsupported_field):
    response = safe_dispatch(
        "deleteAllowance",
        {
            "sessionId": "allowance-test",
            "allowances": [
                {
                    "ownerAccountId": "0.0.1001",
                    unsupported_field: {},
                }
            ],
        },
        1,
    )

    assert response["error"]["code"] == INVALID_PARAMS


def test_build_delete_allowance_groups_serials_by_owner_and_token():
    transaction = _build_delete_allowance_transaction(
        _params(
            [
                {
                    "ownerAccountId": "0.0.1001",
                    "tokenId": "0.0.2001",
                    "serialNumbers": ["1", "2"],
                },
                {
                    "ownerAccountId": "0.0.1001",
                    "tokenId": "0.0.2002",
                    "serialNumbers": ["3"],
                },
            ]
        )
    )

    assert len(transaction.nft_wipe) == 2
    assert transaction.nft_wipe[0].serial_numbers == [1, 2]
    assert transaction.nft_wipe[1].serial_numbers == [3]


def test_empty_delete_allowance_owner_returns_internal_error():
    with patch("tck.handlers.allowance.get_client", return_value=object()):
        response = safe_dispatch(
            "deleteAllowance",
            {
                "sessionId": "allowance-test",
                "allowances": [
                    {
                        "ownerAccountId": "",
                        "tokenId": "0.0.2001",
                        "serialNumbers": ["1"],
                    }
                ],
            },
            1,
        )

    assert response["error"]["code"] == INTERNAL_ERROR


def test_delete_allowance_returns_receipt_status():
    transaction = MagicMock()
    response = transaction.execute.return_value
    response.get_receipt.return_value.status = ResponseCode.SUCCESS

    with (
        patch("tck.handlers.allowance.get_client", return_value=object()),
        patch("tck.handlers.allowance._build_delete_allowance_transaction", return_value=transaction),
    ):
        result = delete_allowance(_params([]))

    assert result.status == "SUCCESS"
    transaction.execute.assert_called_once()
    response.get_receipt.assert_called_once()
