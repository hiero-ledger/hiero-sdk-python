import time
import typing
import grpc
from abc import ABC, abstractmethod
from enum import IntEnum

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.exceptions import MaxAttemptsError

if typing.TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

# Default values for retry and backoff configuration in miliseconds
DEFAULT_MAX_BACKOFF: int = 8000
DEFAULT_MIN_BACKOFF: int = 250
DEFAULT_GRPC_DEADLINE: int = 10000


class _Method:
    """
    Wrapper class for gRPC methods used in transactions and queries.

    This class serves as a container for both transaction and query functions,
    allowing the execution system to handle both types uniformly.
    Each transaction or query type will provide its specific implementation
    via the get_method() function.
    """

    def __init__(
        self,
        query_func: typing.Callable = None,
        transaction_func: typing.Callable = None,
    ):
        """
        Initialize a Method instance with the appropriate callable functions.

        Args:
            query_func (Callable): The gRPC stub method to call for queries
            transaction_func (Callable): The gRPC stub method to call for transactions
        """
        self.query = query_func
        self.transaction = transaction_func


class _ExecutionState(IntEnum):
    """
    Enum representing the possible states of transaction execution.

    These states are used to determine how to handle the response
    from a transaction execution attempt.
    """

    RETRY = 0  # The transaction should be retried
    FINISHED = 1  # The transaction completed successfully
    ERROR = 2  # The transaction failed with an error
    EXPIRED = 3  # The transaction expired before being processed


class _Executable(ABC):
    """
    Abstract base class for all executable operations (transactions and queries).
    
    This class defines the core interface for operations that can be executed on the
    Hedera network. It provides implementations for configuration properties with
    validation (max_backoff, min_backoff, grpc_deadline) and includes
    the execution flow with retry logic.
    
    Subclasses like Transaction will extend this and implement the abstract methods
    to define specific behavior for different types of operations.
    """

    def __init__(self):
        self._max_backoff = None
        self._min_backoff = None
        self._grpc_deadline = None
        self.node_account_id = None

    @property
    def max_backoff(self):
        """Get the maximum backoff time, defaulting to DEFAULT_MAX_BACKOFF if not set."""
        if self._max_backoff is None:
            return DEFAULT_MAX_BACKOFF
        return self._max_backoff

    @max_backoff.setter
    def max_backoff(self, max_backoff):
        """
        Set the maximum backoff time.

        Args:
            max_backoff (int): Maximum backoff time in milliseconds

        Raises:
            ValueError: If max_backoff is negative or less than min_backoff
        """
        if max_backoff is None:
            self._max_backoff = DEFAULT_MAX_BACKOFF
        elif max_backoff < 0:
            raise ValueError("max_backoff must be greater than 0")
        elif max_backoff < self._min_backoff:
            raise ValueError("max_backoff must be greater than min_backoff")
        self._max_backoff = max_backoff
        return self

    @property
    def min_backoff(self):
        """Get the minimum backoff time, defaulting to DEFAULT_MIN_BACKOFF if not set."""
        if self._min_backoff is None:
            return DEFAULT_MIN_BACKOFF
        return self._min_backoff

    @min_backoff.setter
    def min_backoff(self, min_backoff):
        """
        Set the minimum backoff time.

        Args:
            min_backoff (int): Minimum backoff time in milliseconds

        Raises:
            ValueError: If min_backoff is negative or greater than max_backoff
        """
        if min_backoff is None:
            self._min_backoff = DEFAULT_MIN_BACKOFF
        elif min_backoff < 0:
            raise ValueError("min_backoff must be greater than 0")
        elif min_backoff > self._max_backoff:
            raise ValueError("min_backoff must be less than max_backoff")
        self._min_backoff = min_backoff
        return self

    @property
    def grpc_deadline(self):
        """Get the gRPC deadline time."""
        return self._grpc_deadline

    @grpc_deadline.setter
    def grpc_deadline(self, grpc_deadline):
        """
        Set the gRPC deadline time.

        Args:
            grpc_deadline (int): Deadline time in milliseconds

        Raises:
            ValueError: If grpc_deadline is negative
        """
        if grpc_deadline is None:
            self._grpc_deadline = DEFAULT_GRPC_DEADLINE
        elif grpc_deadline < 0:
            raise ValueError("grpc_deadline must be greater than 0")
        self._grpc_deadline = grpc_deadline
        return self

    @abstractmethod
    def should_retry(self, response) -> _ExecutionState:
        """
        Determine whether the operation should be retried based on the response.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        raise NotImplementedError("should_retry must be implemented by subclasses")

    @abstractmethod
    def map_status_error(self, response):
        """
        Maps a response status code to an appropriate error object.
    
        Args:
            response: The response from the network
        
        Returns:
            Exception: An error object representing the error status
        """
        raise NotImplementedError("map_status_error must be implemented by subclasses")

    @abstractmethod
    def make_request(self):
        """
        Build the request object to send to the network.

        Returns:
            The request protobuf object
        """
        raise NotImplementedError("make_request must be implemented by subclasses")

    @abstractmethod
    def get_method(self, channel: _Channel) -> _Method:
        """
        Get the appropriate gRPC method to call for this operation.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the appropriate callable
        """
        raise NotImplementedError("get_method must be implemented by subclasses")

    @abstractmethod
    def map_response(self, response, node_id, proto_request):
        """
        Map the network response to the appropriate response object.

        Args:
            response: The response from the network
            node_id: The ID of the node that processed the request
            proto_request: The protobuf request that was sent

        Returns:
            The appropriate response object for the operation
        """
        raise NotImplementedError("map_response must be implemented by subclasses")

    def _execute(self, client: "Client"):
        """
        Execute a transaction with retry logic.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            TransactionResponse or appropriate response based on transaction type

        Raises:
            Exception: If execution fails with a non-retryable error
        """
        # Determine maximum number of attempts from client or executable
        max_attempts = client.max_attempts
        current_backoff = self.min_backoff
        err_persistant = None

        for attempt in range(max_attempts):
            # Exponential backoff for retries
            if attempt > 0 and current_backoff < self.max_backoff:
                current_backoff *= 2

            # Create a channel wrapper from the client's channel
            channel = _Channel(client.channel)
            
            # Set the node account id to the client's node account id
            self.node_account_id = client.node_account_id

            # Get the appropriate gRPC method to call
            method = self.get_method(channel)

            # Build the request using the executable's make_request method
            proto_request = self.make_request()

            # Call the appropriate method
            # NOTE: Queries do not use these methods currently, only transactions are supported
            try:
                # Execute the transaction method with the protobuf request
                response = _execute_method(method, proto_request)
                
                # Map the response to an error
                status_error = self.map_status_error(response)
                
                # Determine if we should retry based on the response
                execution_state = self.should_retry(response)
                
                # Handle the execution state
                match execution_state:
                    case _ExecutionState.RETRY:
                        # If we should retry, wait for the backoff period and try again
                        err_persistant = status_error
                        _delay_for_attempt(attempt, current_backoff)
                        continue
                    case _ExecutionState.EXPIRED:
                        raise status_error
                    case _ExecutionState.ERROR:
                        raise status_error
                    case _ExecutionState.FINISHED:
                        # If the transaction completed successfully, map the response and return it
                        return self.map_response(response, client.node_account_id, proto_request)
            except grpc.RpcError as e:
                # Save the error
                err_persistant = f"Status: {e.code()}, Details: {e.details()}"
                # Switch to a different node for the next attempt
                node_account_ids = client.get_node_account_ids()
                node_index = (attempt + 1) % len(node_account_ids)
                current_node_account_id = node_account_ids[node_index]
                client._switch_node(current_node_account_id)
                continue
        
        raise MaxAttemptsError("Exceeded maximum attempts for request", client.node_account_id, err_persistant)


def _delay_for_attempt(attempt: int, current_backoff: int):
    """
    Delay for the specified backoff period before retrying.

    Args:
        attempt (int): The current attempt number (0-based)
        current_backoff (int): The current backoff period in milliseconds
    """
    time.sleep(current_backoff * 0.001)

def _execute_method(method, proto_request):
    """
    Executes either a transaction or query method with the given protobuf request.

    Args:
        method (_Method): The method wrapper containing either a transaction or query function
        proto_request: The protobuf request object to pass to the method

    Returns:
        The response from executing the method

    Raises:
        Exception: If neither a transaction nor query method is available to execute
    """
    if method.transaction is not None:
        return method.transaction(proto_request)
    elif method.query is not None:
        return method.query(proto_request)
    raise Exception("No method to execute")