import grpc
from concurrent import futures
from contextlib import contextmanager
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.network import _Node
import socket
from contextlib import closing
from hiero_sdk_python.hapi.services import (
    crypto_service_pb2_grpc,
    token_service_pb2_grpc,
    consensus_service_pb2_grpc,
    schedule_service_pb2_grpc,
    network_service_pb2_grpc,
    file_service_pb2_grpc,
)
from hiero_sdk_python.logger.log_level import LogLevel

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
        self.port = _find_free_port()
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


def _find_free_port():
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
        nodes = []
        for i, server in enumerate(servers):
            nodes.append(_Node(AccountId(0, 0, 3 + i), server.address, None))
        
        # Create network and client
        network = Network(nodes=nodes)
        client = Client(network)
        client.logger.set_level(LogLevel.DISABLED)
        # Set the operator
        key = PrivateKey.generate()
        client.set_operator(AccountId(0, 0, 1800), key)
        client.max_attempts = 4  # Configure for testing
        
        yield client
    finally:
        # Clean up the servers
        for server in servers:
            server.close()
