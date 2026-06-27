"""Tests for the claimToken TCK endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from tck.handlers import token
from tck.handlers.token import _build_claim_token_transaction
from tck.param.token import ClaimTokenParams


pytestmark = pytest.mark.unit

SESSION_ID = "claim-token-test"


def _parse_params(**overrides) -> ClaimTokenParams:
    payload = {
        "sessionId": SESSION_ID,
        "senderAccountId": "0.0.1001",
        "receiverAccountId": "0.0.1002",
        "tokenId": "0.0.2001",
        **overrides,
    }
    return ClaimTokenParams.parse_json_params(payload)


def test_parse_claim_token_params():
    params = _parse_params(serialNumbers=["1", "2"])

    assert params.senderAccountId == "0.0.1001"
    assert params.receiverAccountId == "0.0.1002"
    assert params.tokenId == "0.0.2001"
    assert params.serialNumbers == ["1", "2"]
    assert params.sessionId == SESSION_ID


@pytest.mark.parametrize(
    ("serial_numbers", "message"),
    [
        ("1", "serialNumbers must be a list"),
        ([1], "each serialNumbers item must be a string"),
    ],
)
def test_parse_claim_token_params_validates_serial_numbers(serial_numbers, message):
    with pytest.raises(ValueError, match=message):
        _parse_params(serialNumbers=serial_numbers)


def test_build_fungible_claim_transaction():
    transaction = _build_claim_token_transaction(_parse_params())

    assert isinstance(transaction, TokenClaimAirdropTransaction)
    pending_ids = transaction.get_pending_airdrop_ids()
    assert len(pending_ids) == 1
    assert str(pending_ids[0].sender_id) == "0.0.1001"
    assert str(pending_ids[0].receiver_id) == "0.0.1002"
    assert str(pending_ids[0].token_id) == "0.0.2001"
    assert pending_ids[0].nft_id is None


def test_build_empty_serial_numbers_as_fungible_claim():
    transaction = _build_claim_token_transaction(_parse_params(serialNumbers=[]))

    pending_ids = transaction.get_pending_airdrop_ids()
    assert len(pending_ids) == 1
    assert str(pending_ids[0].token_id) == "0.0.2001"
    assert pending_ids[0].nft_id is None


def test_build_nft_claim_transaction():
    transaction = _build_claim_token_transaction(_parse_params(serialNumbers=["1", "2", "3"]))

    pending_ids = transaction.get_pending_airdrop_ids()
    assert len(pending_ids) == 3
    assert [str(pending_id.nft_id.token_id) for pending_id in pending_ids] == ["0.0.2001"] * 3
    assert [pending_id.nft_id.serial_number for pending_id in pending_ids] == [1, 2, 3]
    assert all(pending_id.token_id is None for pending_id in pending_ids)


def test_build_claim_raises_on_empty_sender_account_id():
    with pytest.raises((ValueError, TypeError)):
        _build_claim_token_transaction(_parse_params(senderAccountId=""))


def test_build_claim_raises_on_empty_receiver_account_id():
    with pytest.raises((ValueError, TypeError)):
        _build_claim_token_transaction(_parse_params(receiverAccountId=""))


def test_build_claim_raises_on_empty_token_id():
    with pytest.raises((ValueError, TypeError)):
        _build_claim_token_transaction(_parse_params(tokenId=""))


def test_build_claim_raises_on_none_sender_account_id():
    with pytest.raises((ValueError, TypeError)):
        _build_claim_token_transaction(_parse_params(senderAccountId=None))


def test_claim_token_executes_transaction_and_returns_status(monkeypatch):
    client = MagicMock()
    transaction = MagicMock(spec=TokenClaimAirdropTransaction)
    transaction_response = transaction.execute.return_value
    receipt = transaction_response.get_receipt.return_value
    receipt.status = ResponseCode.SUCCESS

    monkeypatch.setattr(token, "get_client", MagicMock(return_value=client))
    monkeypatch.setattr(token, "_build_claim_token_transaction", MagicMock(return_value=transaction))

    result = token.claim_token(_parse_params())

    transaction.execute.assert_called_once_with(client, wait_for_receipt=False)
    transaction_response.get_receipt.assert_called_once_with(client, validate_status=True)
    assert result.status == "SUCCESS"


def test_claim_token_applies_common_transaction_params(monkeypatch):
    client = MagicMock()
    transaction = MagicMock(spec=TokenClaimAirdropTransaction)
    transaction_response = transaction.execute.return_value
    receipt = transaction_response.get_receipt.return_value
    receipt.status = ResponseCode.SUCCESS

    monkeypatch.setattr(token, "get_client", MagicMock(return_value=client))
    monkeypatch.setattr(token, "_build_claim_token_transaction", MagicMock(return_value=transaction))

    common_params = MagicMock()
    params = _parse_params()
    params.commonTransactionParams = common_params

    token.claim_token(params)

    common_params.apply_common_params.assert_called_once_with(transaction, client)
