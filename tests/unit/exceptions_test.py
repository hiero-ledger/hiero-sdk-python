import unittest
from unittest.mock import Mock
from hiero_sdk_python.exceptions import PrecheckError, MaxAttemptsError, ReceiptStatusError
from hiero_sdk_python.response_code import ResponseCode

class TestExceptions(unittest.TestCase):
    def test_precheck_error_typing_and_defaults(self):
        """Test PrecheckError with and without optional arguments."""
        # Mock TransactionId
        tx_id_mock = Mock()
        tx_id_mock.__str__ = Mock(return_value="0.0.123@111.222")

        # Case 1: All arguments provided
        err = PrecheckError(ResponseCode.INVALID_TRANSACTION, tx_id_mock, "Custom error")
        self.assertEqual(err.status, ResponseCode.INVALID_TRANSACTION)
        self.assertEqual(err.transaction_id, tx_id_mock)
        self.assertEqual(str(err), "Custom error")
        self.assertEqual(repr(err), f"PrecheckError(status={ResponseCode.INVALID_TRANSACTION}, transaction_id={tx_id_mock})")

        # Case 2: Default message generation
        err_default = PrecheckError(ResponseCode.INVALID_TRANSACTION, tx_id_mock)
        expected_msg = "Transaction failed precheck with status: INVALID_TRANSACTION (1), transaction ID: 0.0.123@111.222"
        self.assertEqual(str(err_default), expected_msg)

    def test_max_attempts_error_typing(self):
        """Test MaxAttemptsError with required and optional arguments."""
        # Case 1: With last_error
        inner_error = ValueError("Connection failed")
        err = MaxAttemptsError("Max attempts reached", "0.0.3", inner_error)
        self.assertEqual(err.node_id, "0.0.3")
        self.assertEqual(err.last_error, inner_error)
        self.assertIn("Max attempts reached", str(err))
        self.assertIn("Connection failed", str(err))

        # Case 2: Without last_error
        err_simple = MaxAttemptsError("Just failed", "0.0.4")
        self.assertEqual(str(err_simple), "Just failed")

    def test_receipt_status_error_typing(self):
        """Test ReceiptStatusError initialization."""
        tx_id_mock = Mock()
        receipt_mock = Mock()
        
        # Case 1: Default message
        err = ReceiptStatusError(ResponseCode.RECEIPT_NOT_FOUND, tx_id_mock, receipt_mock)
        self.assertEqual(err.status, ResponseCode.RECEIPT_NOT_FOUND)
        self.assertEqual(err.transaction_receipt, receipt_mock)
        self.assertIn("RECEIPT_NOT_FOUND", str(err))

        # Case 2: Custom message
        err_custom = ReceiptStatusError(ResponseCode.FAIL_INVALID, tx_id_mock, receipt_mock, "Fatal receipt error")
        self.assertEqual(str(err_custom), "Fatal receipt error")