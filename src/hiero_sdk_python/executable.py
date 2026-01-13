import re
import time
from typing import Callable, Optional, Any, TYPE_CHECKING, List, Union
from abc import ABC, abstractmethod
from enum import IntEnum

import grpc

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import query_pb2
from hiero_sdk_python.response_code import ResponseCode

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client


RST_STREAM = re.compile(
    r"\brst[^0-9a-zA-Z]stream\b",
    re.IGNORECASE | re.DOTALL
)


class _Method:
    """
    Wrapper class for gRPC methods used in transactions and queries.

    This class serves as a container for both transaction and query functions,
    allowing the execution system to handle both types uniformly.
    Each transaction or query type will provide its specific implementation
    via the _get_method() function.
    """

    def __init__(
        self,
        query_func: Optional[Callable[..., Any]] = None,
        transaction_func: Optional[Callable[..., Any]] = None,
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
    
    Subclasses like Transaction and Query will extend this and implement the abstract methods
    to define specific behavior for different types of operations.
    """

    def __init__(self):
        self._max_attempts: Optional[int] = None
        self._max_backoff: Optional[float] = None
        self._min_backoff: Optional[float] = None
        self._grpc_deadline: Optional[float] = None
        self._request_timeout: Optional[float] = None

        self.node_account_id: Optional[AccountId] = None

        self.node_account_ids: List[AccountId] = []
        self._used_node_account_id: Optional[AccountId] = None
        self._node_account_ids_index: int = 0

    def set_node_account_ids(self, node_account_ids: List[AccountId]):
        """Select node account IDs for sending the request."""
        self.node_account_ids = node_account_ids
        return self

    def set_node_account_id(self, node_account_id: AccountId):
        """Convenience wrapper to set a single node account ID."""
        return self.set_node_account_ids([node_account_id])
    
    def set_grpc_deadline(self, grpc_deadline: Union[int, float]):
        """
        Set grpc dedline  for the current transaction.
        """
        if not isinstance(grpc_deadline, (float, int)):
            raise TypeError(f"grpc_deadline must be of type Union[int, float], got {type(grpc_deadline).__name__}")
        
        if grpc_deadline <= 0:
            raise ValueError("grpc_deadline must be greater than 0")
        
        self._grpc_deadline = grpc_deadline
        return self
    
    def set_request_timeout(self, request_timeout: Union[int, float]):
        """
        Set request timeout  for the current transaction.
        """
        if not isinstance(request_timeout, (float, int)):
            raise TypeError(f"request_timeout must be of type Union[int, float], got {type(request_timeout).__name__}")
        
        if request_timeout <= 0:
            raise ValueError("request_timeout must be greater than 0")
        
        self._request_timeout = request_timeout
        return self
    
    def set_min_backoff(self, min_backoff: int):
        """
        Set min backoff  for the current transaction.
        """
        if min_backoff > self._max_backoff:
            raise ValueError("min_backoff cannot be larger than max_backoff")
        
        self._min_backoff = min_backoff
        return self
    
    def set_max_backoff(self, max_backoff: int):
        """
        Set max backoff  for the current transaction.
        """
        if max_backoff < self._max_backoff:
            raise ValueError("max_backoff cannot be smaller than min_backoff")
        
        self._max_backoff = max_backoff
        return self
    
    def set_max_attempts(self, max_attempts: int):
        """
        Set max_attempts for the current transaction.
        """
        if not isinstance(max_attempts, int):
            raise TypeError(f"max_attempts must be of type int, got {(type(max_attempts).__name__)}")
        
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than 0")
        
        self._max_attempts = max_attempts
        return self

    def _select_node_account_id(self) -> Optional[AccountId]:
        """Pick the current node from the list if available, otherwise None."""
        if self.node_account_ids:
            # Use modulo to cycle through the list
            selected = self.node_account_ids[self._node_account_ids_index % len(self.node_account_ids)]
            self._used_node_account_id = selected
            return selected
        return None

    def _advance_node_index(self):
        """Advance to the next node in the list."""
        if self.node_account_ids:
            self._node_account_ids_index += 1

    @abstractmethod
    def _should_retry(self, response) -> _ExecutionState:
        """
        Determine whether the operation should be retried based on the response.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        raise NotImplementedError("_should_retry must be implemented by subclasses")

    @abstractmethod
    def _map_status_error(self, response):
        """
        Maps a response status code to an appropriate error object.
    
        Args:
            response: The response from the network
        
        Returns:
            Exception: An error object representing the error status
        """
        raise NotImplementedError("_map_status_error must be implemented by subclasses")

    @abstractmethod
    def _make_request(self):
        """
        Build the request object to send to the network.

        Returns:
            The request protobuf object
        """
        raise NotImplementedError("_make_request must be implemented by subclasses")

    @abstractmethod
    def _get_method(self, channel: _Channel) -> _Method:
        """
        Get the appropriate gRPC method to call for this operation.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the appropriate callable
        """
        raise NotImplementedError("_get_method must be implemented by subclasses")

    @abstractmethod
    def _map_response(self, response, node_id, proto_request):
        """
        Map the network response to the appropriate response object.

        Args:
            response: The response from the network
            node_id: The ID of the node that processed the request
            proto_request: The protobuf request that was sent

        Returns:
            The appropriate response object for the operation
        """
        raise NotImplementedError("_map_response must be implemented by subclasses")
    
    def _get_request_id(self):
        """
        Format the request ID for the logger.
        """
        return f"{self.__class__.__name__}:{time.time_ns()}"
    
    def _resolve_execution_config(self, client: "Client") -> None:
        """
        Resolve execution configuration by filling unset values from the Client defaults.
        
        Any execution-related configuration explicitly set on this executable
        takes precedence. Missing values are inherited from the provided Client.
        """
        if self._min_backoff is None:
            self._min_backoff = client._min_backoff

        if self._max_backoff is None:
            self._max_backoff = client._max_backoff
        
        if self._grpc_deadline is None:
            self._grpc_deadline = client._grpc_deadline

        if self._request_timeout is None:
            self._request_timeout = client._request_timeout
        
        if self._max_attempts is None:
            self._max_attempts = client.max_attempts

    def _should_retry_exponentially(self, err) -> bool:
        """
        Determine whether a gRPC error represents a failure that should be 
        retried using exponential backoff.
        """
        if not isinstance(err, grpc.RpcError):
            return True

        return (
            err.code() in (
                grpc.StatusCode.DEADLINE_EXCEEDED,
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.RESOURCE_EXHAUSTED,
            ) 
            or (
                err.code() == grpc.StatusCode.INTERNAL 
                and RST_STREAM.search(err.details())
            )
        )
    
    def _get_current_backoff(self, attempts: int):
        return min(
            self._max_backoff, 
            self._min_backoff * (2 ** (attempts + 1))
        )
    
    def _execute(self, client: "Client"):
        """
        Execute a transaction or query with retry logic.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            The response from executing the operation:
                - TransactionResponse: For transaction operations
                - Response: For query operations

        Raises:
            PrecheckError: If the operation fails with a non-retryable error
            MaxAttemptsError: If the operation fails after the maximum number of attempts
            ReceiptStatusError: If the operation fails with a receipt status error
        """
        self._resolve_execution_config(client)

        err_persistant = None
        tx_id = getattr(self, "trasnsaction_id", None)
        
        logger = client.logger
        start = time.time()
        node = None

        for attempt in range(self._max_attempts):
            if start + self._request_timeout <= time.time():
                raise MaxAttemptsError(
                    "Timeout exceeded",
                    node._account_id if node is not None else "No node selected"
                )
                        
            # Select preferred node if provided, fallback to client's default
            selected = self._select_node_account_id()

            node = (
                client.network._get_node(selected)
                if selected is not None
                else client.network.current_node
            )

            if node is None:
                raise ValueError(f"No node found for node_account_id: {selected}")

            #Store for logging and receipts
            self.node_account_id = node._account_id

            # Advance to next node for the next attempt (if using explicit node list)
            self._advance_node_index()

            # Create a channel wrapper from the client's channel
            channel = node._get_channel()
            
            logger.trace("Executing", "requestId", self._get_request_id(), "nodeAccountID", self.node_account_id, "attempt", attempt + 1, "maxAttempts", self._max_attempts)

            # Get the appropriate gRPC method to call
            method = self._get_method(channel)

            # Build the request using the executable's _make_request method
            proto_request = self._make_request()

            if not node.is_healthy():
                # Check if the request is a transaction receipt or record because they are single node requests
                if _is_transaction_receipt_or_record_request(proto_request):
                    _delay_for_attempt(
                        self._get_request_id(),
                        self._get_current_backoff(attempt),
                        attempt,
                        logger,
                        err_persistant
                    )
                    continue

                # raise error `All nodes are unhealthy`
                continue

            try:
                logger.trace("Executing gRPC call", "requestId", self._get_request_id())
                
                # Execute the transaction method with the protobuf request
                response = _execute_method(method, proto_request, self._grpc_deadline)
                
                # Map the response to an error
                status_error = self._map_status_error(response)
                
                # Determine if we should retry based on the response
                execution_state = self._should_retry(response)
                
                logger.trace(f"{self.__class__.__name__} status received", "nodeAccountID", self.node_account_id, "network", client.network.network, "state", execution_state.name, "txID", tx_id)
                
                client.network._decrease_backoff(node)

                # Handle the execution state
                match execution_state:
                    case _ExecutionState.RETRY:
                        if status_error.status == ResponseCode.INVALID_NODE_ACCOUNT:
                            client.network._increase_backoff(node)

                        # If we should retry, wait for the backoff period and try again
                        err_persistant = status_error

                        # If not using explicit node list, switch to next node for retry
                        if not self.node_account_ids:
                            node = client.network._select_node()
                            logger.trace(
                                "Switched to a different node for retry",
                                "error",
                                err_persistant,
                                "from node",
                                self.node_account_id,
                                "to node",
                                node._account_id
                            )

                        _delay_for_attempt(
                            self._get_request_id(),
                            self._get_current_backoff(attempt),
                            attempt,
                            logger,
                            err_persistant
                        )
                        continue
                    case _ExecutionState.EXPIRED:
                        raise status_error
                    case _ExecutionState.ERROR:
                        raise status_error
                    case _ExecutionState.FINISHED:
                        # If the transaction completed successfully, map the response and return it
                        logger.trace(f"{self.__class__.__name__} finished execution")
                        return self._map_response(response, self.node_account_id, proto_request)
            except grpc.RpcError as e:
                logger.trace("Grpc Error Occurs", "error", err_persistant, "from node", self.node_account_id, "to node", node._account_id, "status", e.code())
                
                if not self._should_retry_exponentially(e):
                    raise e
                
                client.network._increase_backoff(node)

                # Save the error
                err_persistant = f"Status: {e.code()}, Details: {e.details()}"
                # If not using explicit node list, switch to next node for retry
                if not self.node_account_ids:
                    node = client.network._select_node()
                    logger.trace("Switched to a different node for the next attempt", "error", err_persistant, "from node", self.node_account_id, "to node", node._account_id)
               
                continue
            
        logger.error("Exceeded maximum attempts for request", "requestId", self._get_request_id(), "last exception being", err_persistant)
        
        raise MaxAttemptsError("Exceeded maximum attempts for request", self.node_account_id, err_persistant)

def _is_transaction_receipt_or_record_request(request):
    if not isinstance(request, query_pb2.Query):
        return False
        
    return (
        request.HasField('transactionGetReceipt') 
        or request.HasField('transactionGetRecord')
    )


def _delay_for_attempt(request_id: str, current_backoff: int, attempt: int, logger, error):
    """
    Delay for the specified backoff period before retrying.

    Args:
        attempt (int): The current attempt number (0-based)
        current_backoff (int): The current backoff period in seconds
    """
    logger.trace(f"Retrying request attempt", "requestId", request_id, "delay", current_backoff, "attempt", attempt, "error", error)
    time.sleep(current_backoff)

def _execute_method(method, proto_request, timeout):
    """
    Executes either a transaction or query method with the given protobuf request.

    Args:
        method (_Method): The method wrapper containing either a transaction or query function
        proto_request: The protobuf request object to pass to the method
        timeout: The grpc deadline (timeout) in seconds

    Returns:
        The response from executing the method

    Raises:
        Exception: If neither a transaction nor query method is available to execute
    """
    if method.transaction is not None:
        return method.transaction(proto_request, timeout=timeout)
    elif method.query is not None:
        return method.query(proto_request, timeout=timeout)
    raise Exception("No method to execute")
