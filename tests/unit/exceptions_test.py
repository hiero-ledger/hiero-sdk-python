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

def test_precheck_error_with_int_status():
    """Test PrecheckError accepts int status for backwards compatibility."""
    tx_id_mock = Mock()
    tx_id_mock.__str__ = Mock(return_value="0.0.123@111.222")

    # Pass int directly (mimicking protobuf field)
    err = PrecheckError(1, tx_id_mock)
    assert err.status == ResponseCode.INVALID_TRANSACTION
    assert isinstance(err.status, ResponseCode)
    assert "INVALID_TRANSACTION" in str(err)

def test_max_attempts_error_typing():
    """Test MaxAttemptsError with required and optional arguments."""
    # Case 1: With last_error as BaseException
    inner_error = ValueError("Connection failed")
    err = MaxAttemptsError("Max attempts reached", "0.0.3", inner_error)
    assert err.node_id == "0.0.3"
    assert err.last_error is inner_error
    assert "Max attempts reached" in str(err)
    assert "Connection failed" in str(err)

    # Case 2: Without last_error
    err_simple = MaxAttemptsError("Just failed", "0.0.4")
    assert str(err_simple) == "Just failed"
    
    # Case 3: With other BaseException types
    runtime_error = RuntimeError("Network timeout")
    err_runtime = MaxAttemptsError("Request failed", "0.0.5", runtime_error)
    assert err_runtime.last_error is runtime_error
    assert "Network timeout" in str(err_runtime)

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

def test_receipt_status_error_with_int_status():
    """Test ReceiptStatusError accepts int status for backwards compatibility."""
    tx_id_mock = Mock()
    receipt_mock = Mock()
    
    # Pass int directly (mimicking protobuf field)
    err = ReceiptStatusError(22, tx_id_mock, receipt_mock)
    assert err.status == ResponseCode.SUCCESS
    assert isinstance(err.status, ResponseCode)
    assert "SUCCESS" in str(err)

def test_receipt_status_error_with_none_transaction_id():
    """Test ReceiptStatusError when transaction_id is None."""
    receipt_mock = Mock()
    
    # Case 1: None transaction_id with default message
    err = ReceiptStatusError(ResponseCode.INVALID_ACCOUNT_ID, None, receipt_mock)
    assert err.status == ResponseCode.INVALID_ACCOUNT_ID
    assert err.transaction_id is None
    assert err.transaction_receipt is receipt_mock
    # Message should not include transaction ID when it's None
    assert "contained error status: INVALID_ACCOUNT_ID" in str(err)
    assert "transaction" not in str(err).split("contained")[0]  # No tx ID before "contained"
    
    # Case 2: None transaction_id with custom message
    err_custom = ReceiptStatusError(ResponseCode.FAIL_INVALID, None, receipt_mock, "No transaction ID available")
    assert err_custom.transaction_id is None
    assert str(err_custom) == "No transaction ID available"

def test_precheck_error_with_none_transaction_id():
    """Test PrecheckError when transaction_id is None."""
    # Case 1: None transaction_id with default message
    err = PrecheckError(ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE, None)
    assert err.status == ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE
    assert err.transaction_id is None
    expected_msg = f"Transaction failed precheck with status: INSUFFICIENT_ACCOUNT_BALANCE ({ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE})"
    assert str(err) == expected_msg
    
    # Case 2: None transaction_id with custom message
    err_custom = PrecheckError(ResponseCode.INVALID_SIGNATURE, None, "Missing transaction context")
    assert err_custom.transaction_id is None
    assert str(err_custom) == "Missing transaction context"