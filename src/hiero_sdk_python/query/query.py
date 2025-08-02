"""
Base class for all network queries. 
"""

import time
from typing import Any, List, Optional, Union

from typing import Any, List, Optional, Union

from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.hapi.services import query_header_pb2, query_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.executable import _Executable, _ExecutionState
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client, Operator
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.executable import _Executable, _ExecutionState, _Method
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    crypto_transfer_pb2,
    duration_pb2,
    query_header_pb2,
    query_pb2,
    transaction_body_pb2,
    transaction_contents_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId


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

    def __init__(self) -> None:
        """
        Initializes the Query with default values.

        Sets timestamp, node account IDs, operator, query payment settings,
        and other properties needed for Hedera queries.
        """

        super().__init__()

        self.timestamp: int = int(time.time())
        self.node_account_ids: List[AccountId] = []
        self.operator: Optional[Operator] = None
        self.node_index: int = 0
        self.payment_amount: Optional[Hbar] = None

    def _get_query_response(self, response: Any) -> query_pb2.Query:
        """
        Extracts the query-specific response object from the full response.

        Subclasses must implement this method to properly extract their
        specific response object.

        Args:
            response (Any): The full response from the network

        Returns:
            The query-specific response object

        Raises:
            NotImplementedError: Always, since subclasses must implement this method
        """
        raise NotImplementedError("_get_query_response must be implemented by subclasses.")

    def set_query_payment(self, payment_amount: Hbar) -> "Query":
        """
        Sets the payment amount for this query.

        Allows the user to override the default query payment for queries that need to be paid.
        If not set, the default is 1 Hbar.

        Args:
            payment_amount (Hbar): The payment amount for this query

        Returns:
            Query: The current query instance for method chaining
        """
        self.payment_amount = payment_amount
        return self

    def _before_execute(self, client: Client) -> None:
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

        # If no payment amount was specified and payment is required for this query,
        # get the cost from the network and set it as the payment amount
        if self.payment_amount is None and self._is_payment_required():
            self.payment_amount = self.get_cost(client)

    def _make_request_header(self) -> query_header_pb2.QueryHeader:
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

        # Default to ANSWER_ONLY response type
        header.responseType = query_header_pb2.ResponseType.ANSWER_ONLY

        # If payment is not required, return header
        if not self._is_payment_required():
            return header

        # If there isn't a user query payment, return COST_ANSWER
        if self.payment_amount is None:
            header.responseType = query_header_pb2.ResponseType.COST_ANSWER
            return header

        if (
            self.operator is not None
            and self.node_account_id is not None
            and self.payment_amount is not None
        ):
            payment_tx = self._build_query_payment_transaction(
                payer_account_id=self.operator.account_id,
                payer_private_key=self.operator.private_key,
                node_account_id=self.node_account_id,
                amount=self.payment_amount,
            )
            header.payment.CopyFrom(payment_tx)

        return header

    def _build_query_payment_transaction(
        self,
        payer_account_id: AccountId,
        payer_private_key: PrivateKey,
        node_account_id: AccountId,
        amount: Hbar,
    ) -> transaction_pb2.Transaction:
        """
        Builds and signs a payment transaction for this query.

        Creates the transaction directly at the service level.

        Args:
            payer_account_id: The account ID of the payer
            payer_private_key: The private key of the payer
            node_account_id: The account ID of the node
            amount (Hbar): The amount to pay

        Returns:
            Transaction: The protobuf Transaction object
        """
        # Create account amounts for the transfer
        account_amounts = [
            basic_types_pb2.AccountAmount(
                accountID=node_account_id._to_proto(),
                amount=amount.to_tinybars(),
            ),
            basic_types_pb2.AccountAmount(
                accountID=payer_account_id._to_proto(),
                amount=-amount.to_tinybars(),
            ),
        ]

        # Generate transaction ID
        transaction_id = TransactionId.generate(payer_account_id)

        # Create transaction body directly
        transaction_body = transaction_body_pb2.TransactionBody(
            transactionID=transaction_id._to_proto(),
            nodeAccountID=node_account_id._to_proto(),
            transactionFee=100_000_000,  # 1 Hbar default fee
            transactionValidDuration=duration_pb2.Duration(seconds=120),
            cryptoTransfer=crypto_transfer_pb2.CryptoTransferTransactionBody(
                transfers=basic_types_pb2.TransferList(accountAmounts=account_amounts)
            ),
        )

        # Serialize transaction body
        body_bytes = transaction_body.SerializeToString()

        # Sign the transaction body
        signature = payer_private_key.sign(body_bytes)
        public_key_bytes = payer_private_key.public_key().to_bytes_raw()

        # Create signature pair
        sig_pair = basic_types_pb2.SignaturePair(
            pubKeyPrefix=public_key_bytes, ed25519=signature
        )

        # Create signature map
        signature_map = basic_types_pb2.SignatureMap(sigPair=[sig_pair])

        # Create signed transaction
        signed_transaction = transaction_contents_pb2.SignedTransaction(
            bodyBytes=body_bytes, sigMap=signature_map
        )

        # Return final transaction
        return transaction_pb2.Transaction(
            signedTransactionBytes=signed_transaction.SerializeToString()
        )

    def get_cost(self, client: Client) -> Hbar:
        """
        Gets the cost of executing this query on the network.

        This method executes a special cost query to determine how many Hbars
        would be required to execute the actual query. The cost query uses
        ResponseType.COST_ANSWER instead of ResponseType.ANSWER_ONLY.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution. Must have an operator set.

        Returns:
            Hbar: The cost in Hbars to execute this query.
                - Returns 0 if no payment is required (_is_payment_required is False),
                  regardless of any manually set payment.
                - Returns the manually set payment amount if one was provided for a paid query.
                - Otherwise, fetches the cost from the network for a paid query.

        Raises:
            ValueError: If the client is None or the client's operator is not set
            PrecheckError: If the cost query fails precheck validation
            MaxAttemptsError: If the cost query fails after maximum retry attempts
            ReceiptStatusError: If the cost query fails with a receipt error
        """
        if not self._is_payment_required():
            return Hbar.from_tinybars(0)

        if self.payment_amount is not None:
            return self.payment_amount

        if client is None or client.operator is None:
            raise ValueError("Client and operator must be set to get the cost")

        # Here we execute the query to get the cost of it
        resp = self._execute(client)
        query_response = self._get_query_response(resp)

        return Hbar.from_tinybars(query_response.header.cost)

    def _get_method(self, channel: _Channel) -> _Method:
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

    def _make_request(self) -> query_pb2.Query:
        """
        Builds the final query request to be sent to the network.

        Subclasses must implement this method to build their specific query request.

        Returns:
            The protobuf query request

        Raises:
            NotImplementedError: Always, since subclasses must implement this method
        """
        raise NotImplementedError("_make_request must be implemented by subclasses.")

    def _map_response(
        self, response: Any, node_id: int, proto_request: query_pb2.Query
    ) -> query_pb2.Query:
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

    def _should_retry(self, response: Any) -> _ExecutionState:
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
            ResponseCode.BUSY,
        }

        if status in retryable_statuses:
            return _ExecutionState.RETRY
        if status == ResponseCode.OK:
            return _ExecutionState.FINISHED
        return _ExecutionState.ERROR

    def _map_status_error(
        self, response: Any
    ) -> Union[PrecheckError, ReceiptStatusError]:
        """
        Maps a response status code to an appropriate error object.

        Args:
            response: The response from the network

        Returns:
            PrecheckError: An error object representing the error status
        """
        query_response = self._get_query_response(response)
        return PrecheckError(query_response.header.nodeTransactionPrecheckCode)

    def _is_payment_required(self) -> bool:
        """
        Determines if query requires payment.

        Returns:
            bool: True if payment is required, False otherwise
        """
        return True
