import pytest
from unittest.mock import Mock
from hiero_sdk_python.exceptions import PrecheckError, MaxAttemptsError, ReceiptStatusError
from hiero_sdk_python.response_code import ResponseCode

pytestmark = pytest.mark.unit

def test_precheck_error_typing_and_defaults():
    """Test PrecheckError with and without optional arguments."""
    # Mock TransactionId
    tx_id_mock = Mock()
    tx_id_mock.__str__ = Mock(return_value="0.0.123@111.222")

    # Case 1: All arguments provided
    err = PrecheckError(ResponseCode.INVALID_TRANSACTION, tx_id_mock, "Custom error")
    assert err.status == ResponseCode.INVALID_TRANSACTION
    assert err.transaction_id is tx_id_mock
    assert str(err) == "Custom error"
    assert repr(err) == f"PrecheckError(status={ResponseCode.INVALID_TRANSACTION}, transaction_id={tx_id_mock})"

    # Case 2: Default message generation
    err_default = PrecheckError(ResponseCode.INVALID_TRANSACTION, tx_id_mock)
    expected_msg = "Transaction failed precheck with status: INVALID_TRANSACTION (1), transaction ID: 0.0.123@111.222"
    assert str(err_default) == expected_msg

def test_max_attempts_error_typing():
    """Test MaxAttemptsError with required and optional arguments."""
    # Case 1: With last_error
    inner_error = ValueError("Connection failed")
    err = MaxAttemptsError("Max attempts reached", "0.0.3", inner_error)
    assert err.node_id == "0.0.3"
    assert err.last_error is inner_error
    assert "Max attempts reached" in str(err)
    assert "Connection failed" in str(err)

    # Case 2: Without last_error
    err_simple = MaxAttemptsError("Just failed", "0.0.4")
    assert str(err_simple) == "Just failed"

def test_receipt_status_error_typing():
    """Test ReceiptStatusError initialization."""
    tx_id_mock = Mock()
    receipt_mock = Mock()
    
    # Case 1: Default message
    err = ReceiptStatusError(ResponseCode.RECEIPT_NOT_FOUND, tx_id_mock, receipt_mock)
    assert err.status == ResponseCode.RECEIPT_NOT_FOUND
    assert err.transaction_receipt is receipt_mock
    assert "RECEIPT_NOT_FOUND" in str(err)

    # Case 2: Custom message
    err_custom = ReceiptStatusError(ResponseCode.FAIL_INVALID, tx_id_mock, receipt_mock, "Fatal receipt error")
    assert str(err_custom) == "Fatal receipt error"