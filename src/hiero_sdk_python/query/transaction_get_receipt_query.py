from typing import Optional,Union,Any

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import transaction_get_receipt_pb2, query_pb2, query_header_pb2, response_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.executable import _Method, _ExecutionState
from hiero_sdk_python.channels import _Channel
import traceback

class TransactionGetReceiptQuery(Query):
    """
    A query to retrieve the receipt of a specific transaction from the Hedera network.

    This class constructs and executes a query to obtain the receipt of a transaction,
    which includes the transaction's status and other pertinent information.
    
    This is one of the few queries that does not require a payment transaction.
    It can be used to check if a transaction has reached consensus and its outcome.
    
    """

    def __init__(self, transaction_id: Optional[TransactionId] = None) -> None:
        """
        Initializes a new instance of the TransactionGetReceiptQuery class.

        Args:
            transaction_id (TransactionId, optional): The ID of the transaction.
        """
        super().__init__()
        self.transaction_id: Optional[TransactionId] = transaction_id
        self._frozen: bool = False

    def _require_not_frozen(self) -> None:
        """
        Ensures the query is not frozen before making changes.
        
        Raises:
            ValueError: If the query is frozen and cannot be modified.
        """
        if self._frozen:
            raise ValueError("This query is frozen and cannot be modified.")

    def set_transaction_id(self, transaction_id: TransactionId) -> "TransactionGetReceiptQuery":
        """
        Sets the transaction ID for which to retrieve the receipt.

        Args:
            transaction_id (TransactionId): The ID of the transaction.

        Returns:
            TransactionGetReceiptQuery: The current instance for method chaining.
            
        Raises:
            ValueError: If the query is frozen and cannot be modified.
        """
        self._require_not_frozen()
        self.transaction_id = transaction_id
        return self

    def freeze(self) -> "TransactionGetReceiptQuery":
        """
        Marks the query as frozen, preventing further modification.
        
        Once frozen, properties like transaction_id cannot be changed.

        Returns:
            TransactionGetReceiptQuery: The current instance for method chaining.
        """
        self._frozen = True
        return self


    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the transaction receipt query.
        
        Builds a TransactionGetReceiptQuery protobuf message with the
        appropriate header and transaction ID.

        Returns:
            query_pb2.Query: The protobuf Query object containing the transaction receipt query.

        Raises:
            ValueError: If the transaction ID is not set.
            AttributeError: If the Query protobuf structure is invalid.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.transaction_id:
                raise ValueError("Transaction ID must be set before making the request.")

            query_header = query_header_pb2.QueryHeader()
            query_header.responseType = query_header_pb2.ResponseType.ANSWER_ONLY

            transaction_get_receipt = transaction_get_receipt_pb2.TransactionGetReceiptQuery()
            transaction_get_receipt.header.CopyFrom(query_header)
            transaction_get_receipt.transactionID.CopyFrom(self.transaction_id._to_proto())

            query = query_pb2.Query()
            if not hasattr(query, 'transactionGetReceipt'):
                raise AttributeError("Query object has no attribute 'transactionGetReceipt'")
            query.transactionGetReceipt.CopyFrom(transaction_get_receipt)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the transaction receipt query.
        
        Implements the abstract method from Query to provide the specific
        gRPC method for getting transaction receipts.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.crypto.getTransactionReceipts
        )

    def _should_retry(self, response: Any) -> _ExecutionState:
        """
        Determines whether the query should be retried based on the response.
        
        Implements the abstract method from Query to decide whether to retry
        the query based on the response status code. First checks the header status,
        then the receipt status.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        status = response.transactionGetReceipt.header.nodeTransactionPrecheckCode
        
        retryable_statuses = {
            ResponseCode.UNKNOWN,
            ResponseCode.BUSY,
            ResponseCode.RECEIPT_NOT_FOUND,
            ResponseCode.RECORD_NOT_FOUND,
            ResponseCode.PLATFORM_NOT_ACTIVE
        }
        
        if status == ResponseCode.OK:
            pass
        elif status in retryable_statuses or status == ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED:
            return _ExecutionState.RETRY
        else:
            return _ExecutionState.ERROR
    
        status = response.transactionGetReceipt.receipt.status
        
        if status in retryable_statuses or status == ResponseCode.OK:
            return _ExecutionState.RETRY
        else:
            return _ExecutionState.FINISHED
        
    def _map_status_error(self, response: Any) -> Union[PrecheckError,ReceiptStatusError]:
        """
        Maps a response status code to an appropriate error object.
        
        Implements the abstract method from Executable to create error objects
        from response status codes. Checks both the header status and receipt status.

        Args:
            response: The response from the network

        Returns:
            PrecheckError: An error object representing the error status
            ReceiptStatusError: An error object representing the receipt status
        """
        status = response.transactionGetReceipt.header.nodeTransactionPrecheckCode
        retryable_statuses = {
            ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
            ResponseCode.BUSY,
            ResponseCode.UNKNOWN,
            ResponseCode.OK
        }
        
        if status not in retryable_statuses:
            return PrecheckError(status)
        
        status = response.transactionGetReceipt.receipt.status
        
        return ReceiptStatusError(status, self.transaction_id, TransactionReceipt._from_proto(response.transactionGetReceipt.receipt, self.transaction_id))
        
    def execute(self, client: Client) -> TransactionReceipt:
        """
        Executes the transaction receipt query.
        
        Sends the query to the Hedera network and processes the response
        to return a TransactionReceipt object.
        
        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            TransactionReceipt: The transaction receipt from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the transaction receipt contains an error status
        """
        self._before_execute(client)
        response = self._execute(client)

        return TransactionReceipt._from_proto(response.transactionGetReceipt.receipt, self.transaction_id)

    def _get_query_response(self, response: response_pb2.Response) -> transaction_get_receipt_pb2.TransactionGetReceiptResponse:
        """
        Extracts the transaction receipt response from the full response.
        
        Implements the abstract method from Query to extract the
        specific transaction receipt response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The transaction get receipt response object
        """
        return response.transactionGetReceipt

    def _is_payment_required(self) -> bool:
        """
        Transaction receipt query does not require payment.
        
        Returns:
            bool: False
        """
        return False