import time
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hapi.services import query_header_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.executable import _Executable, _ExecutionState

class Query(_Executable):
    """
    Base class for all Hedera network queries.

    This class provides common functionality for constructing and executing queries
    to the Hedera network, including attaching a payment transaction if required.
    
    Query objects inherit from _Executable and provide specialized implementations
    for the abstract methods defined there. Subclasses must implement additional
    query-specific methods.
    
    Required implementations for subclasses:
    1. _get_query_response(response) - Extract the specific response from the query
    2. _make_request() - Build the query-specific protobuf request
    3. _get_method(channel) - Return the appropriate gRPC method to call
    """

    def __init__(self):
        """
        Initializes the Query with default values.
        
        Sets timestamp, node account IDs, operator, query payment settings,
        and other properties needed for Hedera queries.
        """
        
        super().__init__()
        
        self.timestamp = int(time.time())
        self.node_account_ids = []
        self.operator = None
        self.node_index = 0
        self._user_query_payment = None
        self._is_payment_required = True
        
    def _get_query_response(self, response):
        """
        Extracts the query-specific response object from the full response.
        
        Subclasses must implement this method to properly extract their
        specific response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The query-specific response object
            
        Raises:
            NotImplementedError: Always, since subclasses must implement this method
        """
        raise NotImplementedError("_get_query_response must be implemented by subclasses.")

    def set_query_payment(self, amount: Hbar):
        """
        Sets the payment amount for this query.
        
        Allows the user to override the default query payment for queries that need to be paid.
        If not set, the default is 1 Hbar.
        
        Args:
            amount (Hbar): The payment amount for this query
            
        Returns:
            Query: The current query instance for method chaining
        """
        self._user_query_payment = amount
        return self

    def _before_execute(self, client):
        """
        Performs setup before executing the query.

        Configures node accounts, operator, and payment details from the client.
        If no payment amount was specified and payment is required for the query,
        gets the cost from the network and sets it as the payment amount.
        
        This method is called automatically before query execution.

        Args:
            client: The client instance to use for execution
        """
        if not self.node_account_ids:
            self.node_account_ids = client.get_node_account_ids()

        self.operator = self.operator or client.operator
        self.node_account_ids = list(set(self.node_account_ids))
        
        # If no payment amount was specified - get the cost (if payment is not required, it was already set to 0 above)
        if self._user_query_payment is None and self._is_payment_required:
            self._user_query_payment = self._get_cost(client)
        
    def _make_request_header(self):
        """
        Constructs the request header for the query.
        
        This includes a payment transaction if we have an operator and node.
        
        If no payment amount is specified and payment is required for the query,
        returns a header with COST_ANSWER response type to get the cost of executing
        the query. Otherwise returns ANSWER_ONLY response type.
        
        Returns:
            QueryHeader: The protobuf QueryHeader object
        """
        header = query_header_pb2.QueryHeader()
        
        # If there isn't a user query payment and payment is required, return COST_ANSWER
        if self._user_query_payment is None and self._is_payment_required:
            header.responseType = query_header_pb2.ResponseType.COST_ANSWER
            return header
        
        header.responseType = query_header_pb2.ResponseType.ANSWER_ONLY

        if (
            self.operator is not None
            and self.node_account_id is not None
            and self._user_query_payment is not None
        ):
            payment_tx = self._build_query_payment_transaction(
                payer_account_id=self.operator.account_id,
                payer_private_key=self.operator.private_key,
                node_account_id=self.node_account_id,
                amount=self._user_query_payment
            )
            header.payment.CopyFrom(payment_tx)

        return header

    def _build_query_payment_transaction(self, payer_account_id, payer_private_key, node_account_id, amount: Hbar):
        """
        Builds and signs a payment transaction for this query.
        
        Uses TransferTransaction to create a payment from the payer to the node.
        
        Args:
            payer_account_id: The account ID of the payer
            payer_private_key: The private key of the payer
            node_account_id: The account ID of the node
            amount (Hbar): The amount to pay
            
        Returns:
            Transaction: The protobuf Transaction object
        """
        tx = TransferTransaction()
        tx.add_hbar_transfer(payer_account_id, -amount.to_tinybars())
        tx.add_hbar_transfer(node_account_id, amount.to_tinybars())

        tx.node_account_id = node_account_id
        tx.transaction_id = TransactionId.generate(payer_account_id)

        body_bytes = tx.build_transaction_body().SerializeToString()
        tx._transaction_body_bytes.setdefault(node_account_id, body_bytes)
        tx.sign(payer_private_key)

        return tx.to_proto()
    
    def _get_cost(self, client):
        """
        Gets the cost of executing this query on the network.
        
        This method executes a special cost query to determine how many Hbars 
        would be required to execute the actual query. The cost query uses
        ResponseType.COST_ANSWER instead of ResponseType.ANSWER_ONLY.
        
        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.
        
        Args:
            client (Client): The client instance to use for execution. Must have an operator set.
        
        Returns:
            Hbar: The cost in Hbars that would be charged to execute this query
            
        Raises:
            ValueError: If the client is None or the client's operator is not set
            PrecheckError: If the cost query fails precheck validation
            MaxAttemptsError: If the cost query fails after maximum retry attempts
            ReceiptStatusError: If the cost query fails with a receipt error
        """
        if client is None or client.operator is None:
            raise ValueError("Client and operator must be set to get the cost")
        
        # Here we execute the query to get the cost of it
        resp = self._execute(client)
        query_response = self._get_query_response(resp)
        
        return Hbar.from_tinybars(query_response.header.cost)
        
    def _get_method(self, channel):
        """
        Returns the appropriate gRPC method for the query.
        
        Subclasses must implement this method to return the specific gRPC method
        for their query type.
        
        Args:
            channel: The channel containing service stubs
            
        Returns:
            _Method: The method wrapper containing the query function
            
        Raises:
            NotImplementedError: Always, since subclasses must implement this method
        """
        raise NotImplementedError("_get_method must be implemented by subclasses.")

    def _make_request(self):
        """
        Builds the final query request to be sent to the network.
        
        Subclasses must implement this method to build their specific query request.
        
        Returns:
            The protobuf query request
            
        Raises:
            NotImplementedError: Always, since subclasses must implement this method
        """
        raise NotImplementedError("_make_request must be implemented by subclasses.")

    def _map_response(self, response, node_id, proto_request):
        """
        Maps the network response to the appropriate response object.
        
        Args:
            response: The response from the network
            node_id: The ID of the node that processed the request
            proto_request: The protobuf request that was sent
            
        Returns:
            The response object
        """
        return response

    def _should_retry(self, response):
        """
        Determines whether the query should be retried based on the response.
        
        This base implementation handles common retry scenarios based on the
        precheck code in the response header.
        
        Args:
            response: The response from the network
            
        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        query_response = self._get_query_response(response)
        status = query_response.header.nodeTransactionPrecheckCode
        
        retryable_statuses = {
            ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
            ResponseCode.PLATFORM_NOT_ACTIVE,
            ResponseCode.BUSY
        }
        
        if status in retryable_statuses:
            return _ExecutionState.RETRY
        elif status == ResponseCode.OK:
            return _ExecutionState.FINISHED
        else:
            return _ExecutionState.ERROR

    def _map_status_error(self, response):
        """
        Maps a response status code to an appropriate error object.
        
        Args:
            response: The response from the network
            
        Returns:
            PrecheckError: An error object representing the error status
        """
        query_response = self._get_query_response(response)
        return PrecheckError(query_response.header.nodeTransactionPrecheckCode)
