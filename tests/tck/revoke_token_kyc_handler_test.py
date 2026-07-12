"""Unit tests for the revokeTokenKyc TCK handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from tck.handlers.token import _build_revoke_kyc_token_transaction, revoke_token_kyc
from tck.param.token import RevokeKycTokenParams
from tck.response.token import RevokeTokenKycResponse


pytestmark = pytest.mark.unit


class TestRevokeKycTokenParams:
    """Tests for RevokeKycTokenParams parsing."""

    def test_parse_json_params_with_all_fields(self):
        """Parse params with tokenId, accountId, and sessionId."""
        params = RevokeKycTokenParams.parse_json_params({
            "tokenId": "0.0.1234",
            "accountId": "0.0.5678",
            "sessionId": "test-session",
        })

        assert params.tokenId == "0.0.1234"
        assert params.accountId == "0.0.5678"
        assert params.sessionId == "test-session"

    def test_parse_json_params_with_session_id(self):
        """Parse params with sessionId."""
        params = RevokeKycTokenParams.parse_json_params({
            "tokenId": "0.0.1234",
            "accountId": "0.0.5678",
            "sessionId": "test-session",
        })

        assert params.tokenId == "0.0.1234"
        assert params.accountId == "0.0.5678"
        assert params.sessionId == "test-session"

    def test_parse_json_params_with_empty_values(self):
        """Parse params with empty string values (edge case from TCK spec)."""
        params = RevokeKycTokenParams.parse_json_params({
            "tokenId": "",
            "accountId": "",
            "sessionId": "test-session",
        })

        assert params.tokenId == ""
        assert params.accountId == ""

    def test_parse_json_params_with_missing_fields(self):
        """Parse params with missing tokenId and accountId."""
        params = RevokeKycTokenParams.parse_json_params({
            "sessionId": "test-session",
        })

        assert params.tokenId is None
        assert params.accountId is None


class TestBuildRevokeKycTransaction:
    """Tests for _build_revoke_kyc_token_transaction."""

    def test_build_with_token_and_account_id(self):
        """Transaction should be built with correct token and account IDs."""
        params = RevokeKycTokenParams(
            tokenId="0.0.1234",
            accountId="0.0.5678",
        )

        transaction = _build_revoke_kyc_token_transaction(params)

        assert isinstance(transaction, TokenRevokeKycTransaction)
        assert transaction.token_id == TokenId.from_string("0.0.1234")
        assert transaction.account_id == AccountId.from_string("0.0.5678")

    def test_build_with_no_token_id(self):
        """Transaction should be built even without tokenId (deferred validation)."""
        params = RevokeKycTokenParams(accountId="0.0.5678")

        transaction = _build_revoke_kyc_token_transaction(params)

        assert isinstance(transaction, TokenRevokeKycTransaction)
        assert transaction.token_id is None
        assert transaction.account_id == AccountId.from_string("0.0.5678")

    def test_build_with_no_account_id(self):
        """Transaction should be built even without accountId (deferred validation)."""
        params = RevokeKycTokenParams(tokenId="0.0.1234")

        transaction = _build_revoke_kyc_token_transaction(params)

        assert isinstance(transaction, TokenRevokeKycTransaction)
        assert transaction.token_id == TokenId.from_string("0.0.1234")
        assert transaction.account_id is None


class TestRevokeTokenKycHandler:
    """Tests for the revoke_token_kyc RPC handler."""

    @patch("tck.handlers.token.get_client")
    def test_handler_returns_success_status(self, mock_get_client):
        """Handler should return the receipt status as response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        with patch.object(TokenRevokeKycTransaction, "execute", return_value=mock_response):
            params = RevokeKycTokenParams(
                tokenId="0.0.1234",
                accountId="0.0.5678",
            )

            result = revoke_token_kyc(params)

        assert isinstance(result, RevokeTokenKycResponse)
        assert result.status == "SUCCESS"

    @patch("tck.handlers.token.get_client")
    def test_handler_returns_failure_status(self, mock_get_client):
        """Handler should propagate non-SUCCESS status codes."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.TOKEN_HAS_NO_KYC_KEY

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        with patch.object(TokenRevokeKycTransaction, "execute", return_value=mock_response):
            params = RevokeKycTokenParams(
                tokenId="0.0.1234",
                accountId="0.0.5678",
            )

            result = revoke_token_kyc(params)

        assert isinstance(result, RevokeTokenKycResponse)
        assert result.status == "TOKEN_HAS_NO_KYC_KEY"

    @patch("tck.handlers.token.get_client")
    def test_handler_applies_common_transaction_params(self, mock_get_client):
        """Handler should apply common transaction params when present."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        mock_common_params = MagicMock()

        with patch.object(TokenRevokeKycTransaction, "execute", return_value=mock_response):
            params = RevokeKycTokenParams(
                tokenId="0.0.1234",
                accountId="0.0.5678",
                commonTransactionParams=mock_common_params,
            )

            revoke_token_kyc(params)

        mock_common_params.apply_common_params.assert_called_once()

    @patch("tck.handlers.token.get_client")
    def test_handler_skips_common_params_when_none(self, mock_get_client):
        """Handler should not fail when commonTransactionParams is None."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        with patch.object(TokenRevokeKycTransaction, "execute", return_value=mock_response):
            params = RevokeKycTokenParams(
                tokenId="0.0.1234",
                accountId="0.0.5678",
                commonTransactionParams=None,
            )

            result = revoke_token_kyc(params)

        assert result.status == "SUCCESS"