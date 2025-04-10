"""Test utilities and mock server implementation for Hedera SDK tests."""

import pytest
import grpc
import socket
from concurrent import futures
from contextlib import closing, contextmanager
from unittest.mock import patch

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    crypto_service_pb2_grpc,
    response_header_pb2,
    response_pb2,
    token_service_pb2_grpc,
    consensus_service_pb2_grpc,
    schedule_service_pb2_grpc,
    network_service_pb2_grpc,
    file_service_pb2_grpc,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode


# ----- Test Utilities -----

def find_free_port():
    """Find a free port on localhost."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class RealRpcError(grpc.RpcError):
    """A more realistic gRPC error for testing."""
    
    def __init__(self, status_code, details):
        self._status_code = status_code
        self._details = details
        
    def code(self):
        return self._status_code
        
    def details(self):
        return self._details


# ----- Mock Server Implementation -----

class MockServer:
    """Mock gRPC server that returns predetermined responses."""
    
    def __init__(self, responses):
        """
        Initialize a mock gRPC server with predetermined responses.
        
        Args:
            responses (list): List of response objects to return in sequence
        """
        self.responses = responses
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.port = find_free_port()
        self.address = f"localhost:{self.port}"
        
        self._register_services()
        
        # Start the server
        self.server.add_insecure_port(self.address)
        self.server.start()
        
    def _register_services(self):
        """Register all necessary gRPC services."""
        # Create and register all servicers
        services = [
            (crypto_service_pb2_grpc.CryptoServiceServicer, 
             crypto_service_pb2_grpc.add_CryptoServiceServicer_to_server),
            (token_service_pb2_grpc.TokenServiceServicer,
             token_service_pb2_grpc.add_TokenServiceServicer_to_server),
            (consensus_service_pb2_grpc.ConsensusServiceServicer,
             consensus_service_pb2_grpc.add_ConsensusServiceServicer_to_server),
            (network_service_pb2_grpc.NetworkServiceServicer,
             network_service_pb2_grpc.add_NetworkServiceServicer_to_server),
            (file_service_pb2_grpc.FileServiceServicer,
             file_service_pb2_grpc.add_FileServiceServicer_to_server),
            (schedule_service_pb2_grpc.ScheduleServiceServicer,
             schedule_service_pb2_grpc.add_ScheduleServiceServicer_to_server),
        ]
        
        for servicer_class, add_servicer_fn in services:
            servicer = self._create_mock_servicer(servicer_class)
            add_servicer_fn(servicer, self.server)
    
    def _create_mock_servicer(self, servicer_class):
        """
        Create a mock servicer that returns predetermined responses.
        
        Args:
            servicer_class: The gRPC servicer class to mock
        
        Returns:
            A mock servicer object
        """
        responses = self.responses
        
        class MockServicer(servicer_class):
            def __getattribute__(self, name):
                # Get special attributes normally
                if name in ('_next_response', '__class__'):
                    return super().__getattribute__(name)
            
                def method_wrapper(request, context):
                    nonlocal responses
                    if not responses:
                        # If no more responses are available, return None
                        return None
                    
                    response = responses.pop(0)
                    
                    if isinstance(response, RealRpcError):
                        # Abort with custom error
                        context.abort(response.code(), response.details())
                    
                    return response
                
                return method_wrapper
                
        return MockServicer()
    
    def close(self):
        """Stop the server."""
        self.server.stop(0)


@contextmanager
def mock_hedera_servers(response_sequences):
    """
    Context manager that creates mock Hedera servers and a client.
    
    Args:
        response_sequences: List of response sequences, one for each mock server
        
    Yields:
        Client: The configured client
    """
    # Create mock servers
    servers = [MockServer(responses) for responses in response_sequences]
    
    try:
        # Configure the network with mock servers
        nodes = [(server.address, AccountId(0, 0, 3 + i)) for i, server in enumerate(servers)]
        
        # Create network and client
        network = Network(nodes=nodes)
        client = Client(network)
        
        # Set the operator
        key = PrivateKey.generate()
        client.set_operator(AccountId(0, 0, 1800), key)
        client.max_attempts = 4  # Configure for testing
        
        yield client
    finally:
        # Clean up the servers
        for server in servers:
            server.close()


# ----- Test Cases -----

def test_retry_success_before_max_attempts():
    """Test that execution succeeds on the last attempt before max_attempts."""
    busy_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.BUSY)
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(
                    shardNum=0,
                    realmNum=0,
                    accountNum=1234
                )
            )
        )
    )

    # First server gives 2 BUSY responses then OK on the 3rd try
    response_sequences = [[busy_response, busy_response, ok_response, receipt_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        # Configure client to allow 3 attempts - should succeed on the last try
        client.max_attempts = 3
        
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        try:
            response = transaction.execute(client)
            receipt = response.get_receipt(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(f"Transaction execution should not raise an exception, but raised: {e}")
        
        assert receipt.status == ResponseCode.SUCCESS


def test_retry_failure_after_max_attempts():
    """Test that execution fails after max_attempts with retriable errors."""
    busy_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.BUSY)

    response_sequences = [[busy_response, busy_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        client.max_attempts = 2
        
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        # Should raise an exception after max attempts
        with pytest.raises(MaxAttemptsError) as excinfo:
            transaction.execute(client)
        
        # Verify the exception contains information about retry exhaustion
        error_message = str(excinfo.value)
        assert "Exceeded maximum attempts" in error_message
        assert "failed precheck with status: BUSY" in error_message


def test_node_switching_after_single_grpc_error():
    """Test that execution switches nodes after receiving a non-retriable error."""
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    error = RealRpcError(grpc.StatusCode.UNAVAILABLE, "Test error")
    
    # First server gives error, second server gives OK
    response_sequences = [
        [error],
        [ok_response],
        [error],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(f"Transaction execution should not raise an exception, but raised: {e}")
        
        # Verify we're now on the second node (index 1)
        assert client.node_account_id == AccountId(0, 0, 4), "Client should have switched to the second node"


def test_node_switching_after_multiple_grpc_errors():
    """Test that execution switches nodes after receiving multiple non-retriable errors."""
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    error_response = RealRpcError(grpc.StatusCode.UNAVAILABLE, "Test error")
    
    response_sequences = [
        [error_response, error_response],
        [error_response, error_response],
        [ok_response, ok_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        try:
            response = transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(f"Transaction execution should not raise an exception, but raised: {e}")
        
        # Verify we're now on the third node (index 2)
        assert client.node_account_id == AccountId(0, 0, 5), "Client should have switched to the third node"


def test_transaction_with_expired_error_not_retried():
    """Test that an expired error is not retried."""
    error_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.TRANSACTION_EXPIRED)
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    
    response_sequences = [
        [error_response],
        [ok_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            transaction.execute(client)
        
        assert str(error_response.nodeTransactionPrecheckCode) in str(exc_info.value)


def test_transaction_with_fatal_error_not_retried():
    """Test that a fatal error is not retried."""
    error_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION_BODY)
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    
    response_sequences = [
        [error_response],
        [ok_response],
    ]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        with pytest.raises(PrecheckError) as exc_info:
            transaction.execute(client)
        
        assert str(error_response.nodeTransactionPrecheckCode) in str(exc_info.value)


def test_exponential_backoff_retry():
    """Test that the retry mechanism uses exponential backoff."""
    busy_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.BUSY)
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    # Create several BUSY responses to force multiple retries
    response_sequences = [[busy_response, busy_response, busy_response, ok_response]]
    
    # Use a mock for time.sleep to capture the delay values
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        client.max_attempts = 5 
        
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(f"Transaction execution should not raise an exception, but raised: {e}")

        # Check that time.sleep was called the expected number of times (3 retries)
        assert mock_sleep.call_count == 3, f"Expected 3 sleep calls, got {mock_sleep.call_count}"
        
        # Verify exponential backoff by checking sleep durations are increasing
        sleep_args = [call_args[0][0] for call_args in mock_sleep.call_args_list]
        
        # Verify each subsequent delay is double than the previous
        for i in range(1, len(sleep_args)):
            assert abs(sleep_args[i] - sleep_args[i-1] * 2) < 0.1, f"Expected doubling delays, but got {sleep_args}"


def test_retriable_error_does_not_switch_node():
    """Test that a retriable error does not switch nodes."""
    busy_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.BUSY)
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    
    response_sequences = [[busy_response, ok_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        transaction = (
            AccountCreateTransaction()
            .set_key(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )
        
        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(f"Transaction execution should not raise an exception, but raised: {e}")
        
        assert client.node_account_id == AccountId(0, 0, 3), "Client should not switch node on retriable errors"