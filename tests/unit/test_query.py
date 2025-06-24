import pytest
from unittest.mock import MagicMock

from hiero_sdk_python.query.query import Query
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.executable import _ExecutionState
from hiero_sdk_python.hapi.services import query_header_pb2, response_pb2, response_header_pb2, crypto_get_account_balance_pb2, token_get_info_pb2
from tests.unit.mock_server import mock_hedera_servers

# By default we test query that doesn't require payment
@pytest.fixture
def query():
    """Fixture for a query that doesn't require payment"""
    return CryptoGetAccountBalanceQuery()

@pytest.fixture
def query_requires_payment():
    """Fixture for a query that requires payment"""
    query = TokenInfoQuery()
    return query

def test_query_initialization(query):
    """Test Query initialization with default values"""
    assert isinstance(query.timestamp, int)
    assert query.node_account_ids == []
    assert query.operator is None
    assert query.node_index == 0
    assert query.payment_amount is None

def test_set_query_payment(query):
    """Test setting custom query payment"""
    payment = Hbar(2)
    result = query.set_query_payment(payment)
    
    assert result == query
    assert query.payment_amount == payment
    
def test_before_execute_payment_not_required(query, mock_client):
    """Test _before_execute method setup for query that doesn't require payment"""
    # payment_amount is None, should not set payment_amount
    query._before_execute(mock_client)
    
    assert query.node_account_ids == mock_client.get_node_account_ids()
    assert query.operator == mock_client.operator
    assert query.payment_amount is None

def test_before_execute_payment_required(query_requires_payment, mock_client):
    """Test _before_execute method setup for query that requires payment"""
    # get_cost() should return Hbar(2)
    mock_get_cost = MagicMock()
    mock_get_cost.return_value = Hbar(2)
    query_requires_payment.get_cost = mock_get_cost
    
    # payment_amount is None, should set payment_amount to 2 Hbars
    query_requires_payment._before_execute(mock_client)
    
    assert query_requires_payment.node_account_ids == mock_client.get_node_account_ids()
    assert query_requires_payment.operator == mock_client.operator
    assert query_requires_payment.payment_amount.to_tinybars() == Hbar(2).to_tinybars()

    # payment_amount is set, should not set payment_amount to 1 Hbars
    mock_get_cost.return_value = Hbar(1)
    query_requires_payment.get_cost = mock_get_cost
    query_requires_payment._before_execute(mock_client)
    
    assert query_requires_payment.payment_amount.to_tinybars() == Hbar(2).to_tinybars()

def test_request_header_no_fields_set(query):
    """Test combinations with no fields set"""
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when no fields are set"
    
def test_request_header_payment_set(query, mock_client):
    """Test combinations with payment set"""
    # Test with only query payment set
    query.payment_amount = Hbar(1)
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
    query.payment_amount = Hbar(1)
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

def test_request_header_payment_zero(query, mock_client):
    """Test that payment field is not present in request header when payment amount is 0"""
    # Set up operator and node account ID from mock client
    query.operator = mock_client.operator
    query.node_account_id = mock_client.network.current_node._account_id
    
    # Test with payment amount set to 0 Hbar
    query.payment_amount = Hbar(0)
    header = query._make_request_header()
    assert not header.HasField('payment'), "Payment field should not be present when payment is set to 0"

def test_make_request_header_with_payment(query_requires_payment, mock_client):
    """Test making request header with payment transaction for queries that require payment"""
    query_requires_payment.operator = mock_client.operator
    query_requires_payment.node_account_id = mock_client.network.current_node._account_id
    query_requires_payment.set_query_payment(Hbar(1))
    
    header = query_requires_payment._make_request_header()
    
    assert isinstance(header, query_header_pb2.QueryHeader)
    assert header.responseType == query_header_pb2.ResponseType.ANSWER_ONLY
    assert header.HasField('payment'), "Payment field should be present when payment is set for queries that require payment"
    
def test_request_header_excludes_payment_for_free_query(query, mock_client):
    """Test that payment is not included in request header for queries that don't require payment"""
    query.operator = mock_client.operator
    query.node_account_id = mock_client.network.current_node._account_id
    # Set query payment to 1 Hbar
    query.set_query_payment(Hbar(1))
    
    # Get header and verify payment was not included
    header = query._make_request_header()
    
    assert isinstance(header, query_header_pb2.QueryHeader)
    assert header.responseType == query_header_pb2.ResponseType.ANSWER_ONLY
    assert not header.HasField('payment'), "Payment field should not be present for queries that don't require payment"

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
    
def test_get_cost_when_payment_not_required(query, mock_client):
    """Test get_cost when payment is not required and is set or not set"""
    # Test without payment_amount
    result = query.get_cost(mock_client)
    assert result.to_tinybars() == Hbar(0).to_tinybars()

    # Test with payment_amount
    query.set_query_payment(Hbar(2))
    result = query.get_cost(mock_client)
    assert result.to_tinybars() == Hbar(0).to_tinybars()

def test_get_cost_when_payment_required_and_set(query_requires_payment, mock_client):
    """Test get_cost when payment is required and set"""
    query_requires_payment.set_query_payment(Hbar(2))
    result = query_requires_payment.get_cost(mock_client)
    assert result.to_tinybars() == Hbar(2).to_tinybars()
    
def test_get_cost_when_payment_required_and_not_set(query_requires_payment, token_id):
    """Test get_cost when payment is required and not set"""
    
    # Create mock response containing cost information (2 tinybars) for token info query
    response = response_pb2.Response(
        tokenGetInfo=token_get_info_pb2.TokenGetInfoResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK,
                responseType=query_header_pb2.ResponseType.COST_ANSWER,
                cost=2
            )
        )
    )
    
    response_sequences = [[response]]
    
    with mock_hedera_servers(response_sequences) as client:
        # Need to set token_id before getting cost, otherwise will fail
        query_requires_payment.set_token_id(token_id)
        result = query_requires_payment.get_cost(client)
        # Verify cost matches expected value of 2 tinybars
        assert result.to_tinybars() == 2
    
def test_query_payment_requirement_defaults_to_true(query_requires_payment):
    """Test that the base Query class and payment-requiring queries default to requiring payment."""
    query = Query()
    assert query._is_payment_required() == True
    # Verify that payment-requiring query also defaults to requiring payment
    assert query_requires_payment._is_payment_required() == True