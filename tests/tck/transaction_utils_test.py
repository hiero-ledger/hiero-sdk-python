"""Unit tests for the execute_validated transaction helper."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.exceptions import ReceiptStatusError
from hiero_sdk_python.response_code import ResponseCode
from tck.util.transaction_utils import execute_validated


pytestmark = pytest.mark.unit


class TestExecuteValidatedSuccess:
    """Test the execute_validated helper's success path."""

    def test_returns_receipt_on_success(self):
        """Test that execute_validated returns the receipt when validation succeeds."""
        mock_receipt = MagicMock()
        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt
        mock_transaction = MagicMock()
        mock_transaction.execute.return_value = mock_response
        mock_client = MagicMock()

        result = execute_validated(mock_transaction, mock_client)

        if result is not mock_receipt:
            raise AssertionError("Expected execute_validated to return the receipt from get_receipt")

        mock_transaction.execute.assert_called_once_with(mock_client, wait_for_receipt=False)
        mock_response.get_receipt.assert_called_once_with(mock_client, validate_status=True)


class TestExecuteValidatedErrors:
    """Test the execute_validated helper's failure path."""

    def test_raises_receipt_status_error_on_failure(self):
        """Test that execute_validated propagates ReceiptStatusError without catching it."""
        mock_transaction_id = MagicMock()
        mock_receipt = MagicMock()
        error = ReceiptStatusError(
            status=ResponseCode.ACCOUNT_DELETED,
            transaction_id=mock_transaction_id,
            transaction_receipt=mock_receipt,
        )

        mock_response = MagicMock()
        mock_response.get_receipt.side_effect = error
        mock_transaction = MagicMock()
        mock_transaction.execute.return_value = mock_response
        mock_client = MagicMock()

        with pytest.raises(ReceiptStatusError) as exc_info:
            execute_validated(mock_transaction, mock_client)

        if exc_info.value.status != ResponseCode.ACCOUNT_DELETED:
            raise AssertionError("Expected the raised error's status to be preserved")
