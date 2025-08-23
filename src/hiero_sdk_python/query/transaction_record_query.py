from typing import Optional, Any, Union
from hiero_sdk_python.hapi.services import query_header_pb2, transaction_get_record_pb2, query_pb2
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord
from hiero_sdk_python.executable import _ExecutionState


class TransactionRecordQuery(Query):
    """
    Represents a query for a transaction record on the Hedera network.
    """

    def __init__(self, transaction_id: Optional[TransactionId] = None):
        """
        Initializes the TransactionRecordQuery with the provided transaction ID.
        """
        super().__init__()
        self.transaction_id : Optional[TransactionId] = transaction_id
        
    def set_transaction_id(self, transaction_id: TransactionId):
        """
        Sets the transaction ID for the query.
        
        Args:
            transaction_id (TransactionId): The ID of the transaction to query.
        Returns:
            TransactionRecordQuery: This query instance.
        """
        self.transaction_id = transaction_id
        return self

    def _make_request(self):
        """
        Constructs the protobuf request for the transaction record query.
        
        Builds a TransactionGetRecordQuery protobuf message with the
        appropriate header and transaction ID.

        Returns:
            Query: The protobuf Query object containing the transaction record query.

        Raises:
            ValueError: If the transaction ID is not set.
            AttributeError: If the Query protobuf structure is invalid.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.transaction_id:
                raise ValueError("Transaction ID must be set before making the request.")

            query_header = self._make_request_header()
            transaction_get_record = transaction_get_record_pb2.TransactionGetRecordQuery()
            transaction_get_record.header.CopyFrom(query_header)
            transaction_get_record.transactionID.CopyFrom(self.transaction_id._to_proto())
            
            query = query_pb2.Query()
            if not hasattr(query, 'transactionGetRecord'):
                raise AttributeError("Query object has no attribute 'transactionGetRecord'")
            query.transactionGetRecord.CopyFrom(transaction_get_record)
            
            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
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
            query_func=channel.crypto.getTxRecordByTxID
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
        status = response.transactionGetRecord.header.nodeTransactionPrecheckCode
        
        retryable_statuses = {
            ResponseCode.UNKNOWN,
            ResponseCode.BUSY,
            ResponseCode.RECEIPT_NOT_FOUND,
            ResponseCode.RECORD_NOT_FOUND,
            ResponseCode.PLATFORM_NOT_ACTIVE
        }
        
        if status == ResponseCode.OK:
            if response.transactionGetRecord.header.responseType == query_header_pb2.ResponseType.COST_ANSWER:
                return _ExecutionState.FINISHED
            pass
        elif status in retryable_statuses or status == ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED:
            return _ExecutionState.RETRY
        else:
            return _ExecutionState.ERROR
    
        status = response.transactionGetRecord.transactionRecord.receipt.status
        
        if status in retryable_statuses or status == ResponseCode.OK:
            return _ExecutionState.RETRY
        elif status == ResponseCode.SUCCESS:
            return _ExecutionState.FINISHED
        else:
            return _ExecutionState.ERROR
        
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
        status = response.transactionGetRecord.header.nodeTransactionPrecheckCode
        retryable_statuses = {
            ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
            ResponseCode.BUSY,
            ResponseCode.UNKNOWN,
            ResponseCode.RECEIPT_NOT_FOUND,
            ResponseCode.RECORD_NOT_FOUND,
            ResponseCode.OK
        }
        
        if status not in retryable_statuses:
            return PrecheckError(status)
        
        receipt = response.transactionGetRecord.transactionRecord.receipt
        
        return ReceiptStatusError(status, self.transaction_id, TransactionReceipt._from_proto(receipt, self.transaction_id))
        
    def execute(self, client):
        """
        Executes the transaction record query.
        
        Sends the query to the Hedera network and processes the response
        to return a TransactionRecord object.
        
        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            TransactionRecord: The transaction record from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the transaction record contains an error status
        """
        self._before_execute(client)
        response = self._execute(client)

        return TransactionRecord._from_proto(response.transactionGetRecord.transactionRecord, self.transaction_id)

    def _get_query_response(self, response: Any):
        """
        Extracts the transaction record response from the full response.
        
        Implements the abstract method from Query to extract the
        specific transaction record response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The transaction get record response object
        """
        return response.transactionGetRecord