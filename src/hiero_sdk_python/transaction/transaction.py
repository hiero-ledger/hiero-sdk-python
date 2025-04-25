import hashlib

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.executable import _Executable, _ExecutionState
from hiero_sdk_python.hapi.services import (basic_types_pb2, transaction_body_pb2, transaction_contents_pb2, transaction_pb2)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (TransactionResponse as TransactionResponseProto)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_response import TransactionResponse


class Transaction(_Executable):
    """
    Base class for all Hedera transactions.

    This class provides common functionality for building, signing, and executing transactions
    on the Hedera network. Subclasses should implement the abstract methods to define
    transaction-specific behavior.

    Required implementations for subclasses:
    1. build_transaction_body() - Build the transaction-specific protobuf body
    2. _get_method(channel) - Return the appropriate gRPC method to call
    """

    def __init__(self):
        """
        Initializes a new Transaction instance with default values.
        """

        super().__init__()

        self.transaction_id = None
        self.transaction_fee = None
        self.transaction_valid_duration = 120 
        self.generate_record = False
        self.memo = ""
        self.transaction_body_bytes = None
        self.signature_map = basic_types_pb2.SignatureMap()
        self._default_transaction_fee = 2_000_000
        self.operator_account_id = None  

    def _make_request(self):
        """
        Implements the Executable._make_request method to build the transaction request.

        This method simply converts the transaction to its protobuf representation
        using the to_proto method.

        Returns:
            Transaction: The protobuf transaction message ready to be sent
        """
        return self.to_proto()

    def _map_response(self, response, node_id, proto_request):
        """
        Implements the Executable._map_response method to create a TransactionResponse.

        This method creates a TransactionResponse object with information about the
        executed transaction, including the transaction ID, node ID, and transaction hash.

        Args:
            response: The response from the network
            node_id: The ID of the node that processed the request
            proto_request: The protobuf request that was sent

        Returns:
            TransactionResponse: The transaction response object

        Raises:
            ValueError: If proto_request is not a Transaction
        """
        if not isinstance(proto_request, transaction_pb2.Transaction):
            return ValueError(f"Expected Transaction but got {type(proto_request)}")

        hash_obj = hashlib.sha384()
        hash_obj.update(proto_request.signedTransactionBytes)
        tx_hash = hash_obj.digest()
        transaction_response = TransactionResponse()
        transaction_response.transaction_id = self.transaction_id
        transaction_response.node_id = node_id
        transaction_response.hash = tx_hash

        return transaction_response

    def _should_retry(self, response):
        """
        Implements the Executable._should_retry method to determine if a transaction should be retried.

        This method examines the response status code to determine if the transaction
        should be retried, is finished, expired, or has an error.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        if not isinstance(response, TransactionResponseProto):
            raise ValueError(f"Expected TransactionResponseProto but got {type(response)}")

        status = response.nodeTransactionPrecheckCode

        # Define status codes that indicate the transaction should be retried
        retryable_statuses = {
            ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
            ResponseCode.PLATFORM_NOT_ACTIVE,
            ResponseCode.BUSY,
        }

        if status in retryable_statuses:
            return _ExecutionState.RETRY

        if status == ResponseCode.TRANSACTION_EXPIRED:
            return _ExecutionState.EXPIRED

        if status == ResponseCode.OK:
            return _ExecutionState.FINISHED

        return _ExecutionState.ERROR

    def _map_status_error(self, response):
        """
        Maps a transaction response to a corresponding PrecheckError exception.

        Args:
            response (TransactionResponseProto): The transaction response from the network

        Returns:
            PrecheckError: An exception containing the error code and transaction ID
        """
        error_code = response.nodeTransactionPrecheckCode
        tx_id = self.transaction_id
        
        return PrecheckError(error_code, tx_id)

    def sign(self, private_key):
        """
        Signs the transaction using the provided private key.

        Args:
            private_key (PrivateKey): The private key to sign the transaction with.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If the transaction body has not been built.
        """
        if self.transaction_body_bytes is None:
            self.transaction_body_bytes = self.build_transaction_body().SerializeToString()

        signature = private_key.sign(self.transaction_body_bytes)

        public_key_bytes = private_key.public_key().to_bytes_raw()

        sig_pair = basic_types_pb2.SignaturePair(
            pubKeyPrefix=public_key_bytes,
            ed25519=signature
        )

        self.signature_map.sigPair.append(sig_pair)

        return self

    def to_proto(self):
        """
        Converts the transaction to its protobuf representation.

        Returns:
            Transaction: The protobuf Transaction message.

        Raises:
            Exception: If the transaction body has not been built.
        """
        if self.transaction_body_bytes is None:
            raise Exception("Transaction must be signed before calling to_proto()")

        signed_transaction = transaction_contents_pb2.SignedTransaction(
            bodyBytes=self.transaction_body_bytes,
            sigMap=self.signature_map
        )

        return transaction_pb2.Transaction(
            signedTransactionBytes=signed_transaction.SerializeToString()
        )

    def freeze_with(self, client):
        """
        Freezes the transaction by building the transaction body and setting necessary IDs.

        Args:
            client (Client): The client instance to use for setting defaults.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If required IDs are not set.
        """
        if self.transaction_body_bytes is not None:
            return self

        if self.transaction_id is None:
            self.transaction_id = client.generate_transaction_id()

        if self.node_account_id is None:
            self.node_account_id = client.network.current_node._account_id

        # print(f"Transaction's node account ID set to: {self.node_account_id}")
        self.transaction_body_bytes = self.build_transaction_body().SerializeToString()

        return self

    def execute(self, client):
        """
        Executes the transaction on the Hedera network using the provided client.

        This function delegates the core logic to `_execute()` and `get_receipt()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution.

        Returns:
            TransactionReceipt: The receipt of the transaction.

        Raises:
            PrecheckError: If the transaction/query fails with a non-retryable error
            MaxAttemptsError: If the transaction/query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        if self.transaction_body_bytes is None:
            self.freeze_with(client)

        if self.operator_account_id is None:
            self.operator_account_id = client.operator_account_id

        if not self.is_signed_by(client.operator_private_key.public_key()):
            self.sign(client.operator_private_key)

        # Call the _execute function from executable.py to handle the actual execution
        response = self._execute(client)

        response.validate_status = True
        response.transaction = self
        response.transaction_id = self.transaction_id

        return response.get_receipt(client)

    def is_signed_by(self, public_key):
        """
        Checks if the transaction has been signed by the given public key.

        Args:
            public_key (PublicKey): The public key to check.

        Returns:
            bool: True if signed by the given public key, False otherwise.
        """
        public_key_bytes = public_key.to_bytes_raw()

        for sig_pair in self.signature_map.sigPair:
            if sig_pair.pubKeyPrefix == public_key_bytes:
                return True
        return False

    def build_transaction_body(self):
        """
        Abstract method to build the transaction body.

        Subclasses must implement this method to construct the transaction-specific
        body and include it in the overall TransactionBody.

        Returns:
            TransactionBody: The protobuf TransactionBody message.

        Raises:
            NotImplementedError: Always, since subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement build_transaction_body()")
    
    def build_base_transaction_body(self):
        """
        Builds the base transaction body including common fields.

        Returns:
            TransactionBody: The protobuf TransactionBody message with common fields set.

        Raises:
            ValueError: If required IDs are not set.
        """
        if self.transaction_id is None:
                if self.operator_account_id is None:
                    raise ValueError("Operator account ID is not set.")
                self.transaction_id = TransactionId.generate(self.operator_account_id)

        transaction_id_proto = self.transaction_id.to_proto()

        if self.node_account_id is None:
            raise ValueError("Node account ID is not set.")

        transaction_body = transaction_body_pb2.TransactionBody()
        transaction_body.transactionID.CopyFrom(transaction_id_proto)
        transaction_body.nodeAccountID.CopyFrom(self.node_account_id.to_proto())

        transaction_body.transactionFee = self.transaction_fee or self._default_transaction_fee

        transaction_body.transactionValidDuration.seconds = self.transaction_valid_duration
        transaction_body.generateRecord = self.generate_record
        transaction_body.memo = self.memo

        return transaction_body

    def _require_not_frozen(self):
        """
        Ensures the transaction is not frozen before allowing modifications.

        Raises:
            Exception: If the transaction has already been frozen.
        """
        if self.transaction_body_bytes is not None:
            raise Exception("Transaction is immutable; it has been frozen.")

    def set_transaction_memo(self, memo):
        """
        Sets the memo field for the transaction.

        Args:
            memo (str): The memo string to attach to the transaction.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If the transaction has already been frozen.
        """
        self._require_not_frozen()
        self.memo = memo
        return self
