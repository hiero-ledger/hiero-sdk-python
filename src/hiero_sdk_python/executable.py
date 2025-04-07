import time
import typing
from abc import ABC, abstractmethod
from enum import IntEnum

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.transaction.transaction_response import TransactionResponse

if typing.TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

# Default values for retry and backoff configuration in seconds
DEFAULT_MAX_BACKOFF: int = 8
DEFAULT_MIN_BACKOFF: int = 1
DEFAULT_GRPC_DEADLINE: int = 10
DEFAULT_MAX_RETRY: int = 10


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
    validation (max_backoff, min_backoff, grpc_deadline, max_retry) and includes
    the execution flow with retry logic.
    
    Subclasses like Transaction will extend this and implement the abstract methods
    to define specific behavior for different types of operations.
    """

    def __init__(self):
        self._max_backoff = None
        self._min_backoff = None
        self._grpc_deadline = None
        self._max_retry = None

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
            max_backoff (int): Maximum backoff time in seconds

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
            min_backoff (int): Minimum backoff time in seconds

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
            grpc_deadline (int): Deadline time in seconds

        Raises:
            ValueError: If grpc_deadline is negative
        """
        if grpc_deadline is None:
            self._grpc_deadline = DEFAULT_GRPC_DEADLINE
        elif grpc_deadline < 0:
            raise ValueError("grpc_deadline must be greater than 0")
        self._grpc_deadline = grpc_deadline
        return self

    @property
    def max_retry(self):
        """Get the maximum number of retry attempts."""
        return self._max_retry

    @max_retry.setter
    def max_retry(self, max_retry):
        """
        Set the maximum number of retry attempts.

        Args:
            max_retry (int): Maximum number of retry attempts

        Raises:
            ValueError: If max_retry is negative
        """
        if max_retry is None:
            self._max_retry = DEFAULT_MAX_RETRY
        elif max_retry < 0:
            raise ValueError("max_retry must be greater than 0")
        self._max_retry = max_retry
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
            executable (Executable): The transaction to execute

        Returns:
            TransactionResponse or appropriate response based on transaction type

        Raises:
            Exception: If execution fails with a non-retryable error
        """
        # Determine maximum number of attempts from client or executable
        if client.max_attempts is not None:
            max_attempts = client.max_attempts
        else:
            max_attempts = self.max_retry

        current_backoff = self.min_backoff

        for attempt in range(max_attempts):
            # Exponential backoff for retries
            if attempt > 0 and current_backoff < self.max_backoff:
                current_backoff *= current_backoff

            # Create a channel wrapper from the client's channel
            channel = _Channel(client.channel)
            
            # Get the appropriate gRPC method to call
            method = self.get_method(channel)

            # Build the request using the executable's make_request method
            proto_request = self.make_request()

            # Call the appropriate method
            # Note: Queries do not use these methods currently, only transactions are supported
            if method.transaction is not None:
                response = method.transaction(proto_request)
            elif method.query is not None:
                response = method.query(proto_request)
            
            # Determine if we should retry based on the response
            execution_state = self.should_retry(response)
            
            # Handle the execution state
            match execution_state:
                case _ExecutionState.RETRY:
                    # If we should retry, wait for the backoff period and try again
                    _delay_for_attempt(attempt, current_backoff)
                    continue
                case _ExecutionState.EXPIRED:
                    # TODO: handle errors
                    return TransactionResponse()
                case _ExecutionState.ERROR:
                    # TODO: handle errors
                    return TransactionResponse()
                case _ExecutionState.FINISHED:
                    # If the transaction completed successfully, map the response and return it
                    # TODO: node_id should be passed here instead of empty AccountId()
                    return self.map_response(response, AccountId(), proto_request)

        # If we've exhausted all retry attempts, return an empty response
        return TransactionResponse()


def _delay_for_attempt(attempt: int, current_backoff: int):
    """
    Delay for the specified backoff period before retrying.

    Args:
        attempt (int): The current attempt number (0-based)
        current_backoff (int): The current backoff period in seconds
    """
    time.sleep(current_backoff)
