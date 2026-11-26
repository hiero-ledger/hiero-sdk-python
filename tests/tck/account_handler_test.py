"""Tests for TCK account handler response mapping."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_info import AccountInfo
from hiero_sdk_python.crypto.private_key import PrivateKey
from tck.handlers.account import _build_account_info_response
from tck.handlers.registry import parse_result
from tck.util.key_utils import key_to_string


pytestmark = pytest.mark.unit


def test_build_account_info_response_maps_alias_ledger_id_and_ethereum_nonce():
    """AccountInfo fields should be serialized into the TCK response formats."""
    alias = PrivateKey.generate_ed25519().public_key()
    info = AccountInfo(alias=alias, ledger_id=b"\x01\x02\xff", ethereum_nonce=42)

    response = _build_account_info_response(info)

    assert response.aliasKey == key_to_string(alias)
    assert response.ledgerId == "0102ff"
    assert response.ethereumNonce == "42"


def test_build_account_info_response_handles_missing_alias_ledger_and_nonce():
    """Missing optional values should not raise and should retain TCK defaults."""
    response = _build_account_info_response(AccountInfo())

    assert response.aliasKey is None
    assert response.ledgerId is None
    assert response.ethereumNonce == "0"

    serialized = parse_result(response)
    assert "aliasKey" not in serialized
    assert "ledgerId" not in serialized
    assert serialized["ethereumNonce"] == "0"
