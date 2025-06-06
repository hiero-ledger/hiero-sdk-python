import pytest

from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.executable import _ExecutionState
from hiero_sdk_python.hapi.services import query_header_pb2, response_pb2, response_header_pb2, crypto_get_account_balance_pb2

@pytest.fixture
def query():
    return CryptoGetAccountBalanceQuery()

def test_query_initialization(query):
    """Test Query initialization with default values"""
    assert isinstance(query.timestamp, int)
    assert query.node_account_ids == []
    assert query.operator is None
    assert query.node_index == 0
    assert query._user_query_payment is None
    assert query._default_query_payment.to_tinybars() == Hbar(1).to_tinybars()

def test_set_query_payment(query):
    """Test setting custom query payment"""
    payment = Hbar(2)
    result = query.set_query_payment(payment)
    
    assert result == query
    assert query._user_query_payment == payment

def test_before_execute_sets_defaults(query, mock_client):
    """Test _before_execute method setup"""
    query._before_execute(mock_client)
    
    assert query.node_account_ids == mock_client.get_node_account_ids()
    assert query.operator == mock_client.operator
    assert query._user_query_payment == query._default_query_payment
    
    # Verify the custom payment is used and default is not
    payment = Hbar(2)
    query.set_query_payment(payment)
    query._before_execute(mock_client)
    
    assert query._user_query_payment == payment

def test_request_header_no_fields_set(query):
    """Test combinations with no fields set"""
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when no fields are set"
    
def test_request_header_payment_set(query, mock_client):
    """Test combinations with payment set"""
    # Test with only query payment set
    query._user_query_payment = Hbar(1)
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only query payment is set"
    
    # Test with query payment and operator set
    query.operator = mock_client.operator
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only operator and payment are set"

def test_request_header_node_account_set(query, mock_client):
    """Test combinations with node account set"""
    # Test with just node account set
    query.node_account_id = mock_client.network.current_node._account_id
    
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only node account is set"

    # Test with node account and query payment set
    query._user_query_payment = Hbar(1)
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only node account and payment are set"

def test_request_header_operator_set(query, mock_client):
    """Test combinations with operator set"""
    # Test with just operator set
    query.operator = mock_client.operator
    
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only operator is set"

    # Test with operator and node account set
    query.node_account_id = mock_client.network.current_node._account_id
    
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when only operator and node account are set"

def test_make_request_header_with_payment(query, mock_client):
    """Test making request header with payment transaction"""
    # Setup
    query.operator = mock_client.operator
    query.node_account_id = mock_client.network.current_node._account_id
    query.set_query_payment(Hbar(1))
    
    header = query._make_request_header()
    
    assert isinstance(header, query_header_pb2.QueryHeader)
    assert header.responseType == query_header_pb2.ResponseType.ANSWER_ONLY
    assert header.HasField('payment')

def test_should_retry_retryable_statuses(query):
    """Test that retryable status codes trigger retry"""
    # Test each retryable status
    retryable_statuses = [
        ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
        ResponseCode.PLATFORM_NOT_ACTIVE,
        ResponseCode.BUSY
    ]
    
    for status in retryable_statuses:
        response = response_pb2.Response(
        cryptogetAccountBalance=crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=status
            )
        )
    )
        
        result = query._should_retry(response)
        assert result == _ExecutionState.RETRY, f"Status {status} should trigger retry"

def test_should_retry_ok_status(query):
    """Test that OK status finishes execution"""
    response = response_pb2.Response(
        cryptogetAccountBalance=crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            )
        )
    )
    
    result = query._should_retry(response)
    assert result == _ExecutionState.FINISHED

def test_should_retry_error_status(query):
    """Test that non-retryable error status triggers error state"""
    response = response_pb2.Response(
        cryptogetAccountBalance=crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION
            )
        )
    )
    
    result = query._should_retry(response)
    assert result == _ExecutionState.ERROR