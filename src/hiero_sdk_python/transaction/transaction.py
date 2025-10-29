import hashlib
from typing import Optional

from typing import TYPE_CHECKING

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.executable import _Executable, _ExecutionState
from hiero_sdk_python.hapi.services import (basic_types_pb2, transaction_pb2, transaction_contents_pb2, transaction_pb2)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import SchedulableTransactionBody
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (TransactionResponse as TransactionResponseProto)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_response import TransactionResponse

if TYPE_CHECKING:
    from hiero_sdk_python.schedule.schedule_create_transaction import (
        ScheduleCreateTransaction,
    )
    from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit


class Transaction(_Executable):
    """
    Base class for all Hedera transactions.

    This class provides common functionality for building, signing, and executing transactions
    on the Hedera network. Subclasses should implement the abstract methods to define
    transaction-specific behavior.

    Required implementations for subclasses:
    1. build_transaction_body() - Build the transaction-specific protobuf body
    2. build_scheduled_body() - Build the schedulable transaction-specific protobuf body
    3. _get_method(channel) - Return the appropriate gRPC method to call
    """

    def __init__(self) -> None:
        """
        Initializes a new Transaction instance with default values.
        """

        super().__init__()

        self.transaction_id = None
        self.transaction_fee: int | None = None
        self.transaction_valid_duration = 120 
        self.generate_record = False
        self.memo = ""
        self.custom_fee_limits: list[CustomFeeLimit] = []
        # Maps each node's AccountId to its corresponding transaction body bytes
        # This allows us to maintain separate transaction bodies for each node
        # which is necessary in case node is unhealthy and we have to switch it with other node.
        # Each transaction body has the AccountId of the node it's being submitted to.
        # If these do not match `INVALID_NODE_ACCOUNT` error will occur.
        self._transaction_body_bytes: dict[AccountId, bytes] = {}
        
        # Maps transaction body bytes to their associated signatures
        # This allows us to maintain the signatures for each unique transaction
        # and ensures that the correct signatures are used when submitting transactions
        self._signature_map: dict[bytes, basic_types_pb2.SignatureMap] = {}
        self._default_transaction_fee = 2_000_000
        self.operator_account_id = None  

    def _make_request(self):
        """
        Implements the Executable._make_request method to build the transaction request.

        This method simply converts the transaction to its protobuf representation
        using the _to_proto method.

        Returns:
            Transaction: The protobuf transaction message ready to be sent
        """
        return self._to_proto()

    def _map_response(
            self, 
            response, 
            node_id, 
            proto_request):
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
        # We require the transaction to be frozen before signing
        self._require_frozen()
        
        # We sign the bodies for each node in case we need to switch nodes during execution.
        for body_bytes in self._transaction_body_bytes.values():
            signature = private_key.sign(body_bytes)

            public_key_bytes = private_key.public_key().to_bytes_raw()

            if private_key.is_ed25519():
                sig_pair = basic_types_pb2.SignaturePair(
                    pubKeyPrefix=public_key_bytes,
                    ed25519=signature
                )
            else:
                sig_pair = basic_types_pb2.SignaturePair(
                    pubKeyPrefix=public_key_bytes,
                    ECDSA_secp256k1=signature
                )

            # We initialize the signature map for this body_bytes if it doesn't exist yet
            self._signature_map.setdefault(body_bytes, basic_types_pb2.SignatureMap())

            # Append the signature pair to the signature map for this transaction body
            self._signature_map[body_bytes].sigPair.append(sig_pair)
        
        return self

    def _to_proto(self):
        """
        Converts the transaction to its protobuf representation.

        Returns:
            Transaction: The protobuf Transaction message.

        Raises:
            Exception: If the transaction body has not been built.
        """
        # We require the transaction to be frozen before converting to protobuf
        self._require_frozen()

        body_bytes = self._transaction_body_bytes.get(self.node_account_id)
        if body_bytes is None:
            raise ValueError(f"No transaction body found for node {self.node_account_id}")

        # Get signature map, or create empty one if transaction is not signed
        sig_map = self._signature_map.get(body_bytes)
        if sig_map is None:
            sig_map = basic_types_pb2.SignatureMap()

        signed_transaction = transaction_contents_pb2.SignedTransaction(
            bodyBytes=body_bytes,
            sigMap=sig_map
        )

        return transaction_pb2.Transaction(
            signedTransactionBytes=signed_transaction.SerializeToString()
        )

    def freeze(self):
        """
        Freezes the transaction by building the transaction body and setting necessary IDs.

        This method requires that transaction_id and node_account_id are already set manually.
        Use freeze_with(client) if you want to use the client to set these values automatically.

        IMPORTANT: This method only builds the transaction body for the single node specified
        in node_account_id. If you later execute this transaction and the network needs to retry
        with a different node, the transaction will fail. For production use with automatic node
        failover, use freeze_with(client) instead.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            ValueError: If transaction_id or node_account_id are not set.
        """
        if self._transaction_body_bytes:
            return self
        
        if self.transaction_id is None:
            raise ValueError("Transaction ID must be set before freezing. Use freeze_with(client) or set_transaction_id().")
        
        if self.node_account_id is None:
            raise ValueError("Node account ID must be set before freezing. Use freeze_with(client) or manually set node_account_id.")
        
        # Build the transaction body for the single node
        self._transaction_body_bytes[self.node_account_id] = self.build_transaction_body().SerializeToString()
        
        return self

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
        if self._transaction_body_bytes:
            return self
        
        if self.transaction_id is None:
            self.transaction_id = client.generate_transaction_id()
        
        # We iterate through every node in the client's network
        # For each node, set the node_account_id and build the transaction body
        # This allows the transaction to be submitted to any node in the network
        for node in client.network.nodes:
            self.node_account_id = node._account_id
            self._transaction_body_bytes[node._account_id] = self.build_transaction_body().SerializeToString()
        
        # Set the node account id to the current node in the network
        self.node_account_id = client.network.current_node._account_id
        
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
        if not self._transaction_body_bytes:
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
        
        sig_map = self._signature_map.get(self._transaction_body_bytes.get(self.node_account_id))
        
        if sig_map is None:
            return False
        
        for sig_pair in sig_map.sigPair:
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

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Abstract method to build the schedulable transaction body.

        Subclasses must implement this method to construct the transaction-specific
        body and include it in the overall SchedulableTransactionBody.

        Returns:
            SchedulableTransactionBody: The protobuf SchedulableTransactionBody message.

        Raises:
            NotImplementedError: Always, since subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement build_scheduled_body()")

    def build_base_transaction_body(self) -> transaction_pb2.TransactionBody:
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

        transaction_id_proto = self.transaction_id._to_proto()

        if self.node_account_id is None:
            raise ValueError("Node account ID is not set.")

        transaction_body = transaction_pb2.TransactionBody()
        transaction_body.transactionID.CopyFrom(transaction_id_proto)
        transaction_body.nodeAccountID.CopyFrom(self.node_account_id._to_proto())

        transaction_body.transactionFee = self.transaction_fee or self._default_transaction_fee

        transaction_body.transactionValidDuration.seconds = self.transaction_valid_duration
        transaction_body.generateRecord = self.generate_record
        transaction_body.memo = self.memo
        custom_fee_limits = [custom_fee._to_proto() for custom_fee in self.custom_fee_limits]
        transaction_body.max_custom_fees.extend(custom_fee_limits)

        return transaction_body

    def build_base_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the base scheduled transaction body including common fields.

        Returns:
            SchedulableTransactionBody:
                The protobuf SchedulableTransactionBody message with common fields set.
        """
        schedulable_body = SchedulableTransactionBody()
        schedulable_body.transactionFee = (
            self.transaction_fee or self._default_transaction_fee
        )
        schedulable_body.memo = self.memo
        custom_fee_limits = [custom_fee._to_proto() for custom_fee in self.custom_fee_limits]
        schedulable_body.max_custom_fees.extend(custom_fee_limits)

        return schedulable_body

    def schedule(self) -> "ScheduleCreateTransaction":
        """
        Converts this transaction into a scheduled transaction.

        This method prepares the current transaction to be scheduled for future execution
        via the network's scheduling service. It returns a `ScheduleCreateTransaction`
        instance with the transaction's details embedded as a schedulable transaction body.

        Returns:
            ScheduleCreateTransaction: A new instance representing the scheduled version
                of this transaction, ready to be configured and submitted.

        Raises:
            Exception: If the transaction has already been frozen and cannot be scheduled.
        """
        self._require_not_frozen()

        # The import is here to avoid circular dependency
        # pylint: disable=import-outside-toplevel
        from hiero_sdk_python.schedule.schedule_create_transaction import (
            ScheduleCreateTransaction,
        )

        schedulable_body = self.build_scheduled_body()
        return ScheduleCreateTransaction()._set_schedulable_body(schedulable_body)

    def _require_not_frozen(self) -> None:
        """
        Ensures the transaction is not frozen before allowing modifications.

        Raises:
            Exception: If the transaction has already been frozen.
        """
        if self._transaction_body_bytes:
            raise Exception("Transaction is immutable; it has been frozen.")

    def _require_frozen(self) -> None:
        """
        Ensures the transaction is frozen before allowing operations that require a frozen transaction.

        This method checks if the transaction has been frozen by verifying that transaction_body_bytes
        has been set.

        Raises:
            Exception: If the transaction has not been frozen yet.
        """
        if not self._transaction_body_bytes:
            raise Exception("Transaction is not frozen")

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

    def set_transaction_id(self, transaction_id: TransactionId):
        """
        Sets the transaction ID for the transaction.

        Args:
            transaction_id (TransactionId): The transaction ID to set.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If the transaction has already been frozen.
        """
        self._require_not_frozen()
        self.transaction_id = transaction_id
        return self

    def to_bytes(self):
        """
        Serializes the frozen transaction into its protobuf-encoded byte representation.

        This method is equivalent to the TypeScript SDK's transaction.toBytes() method.
        The transaction must be frozen before calling this method.

        The transaction can be serialized with or without signatures:
        - **Unsigned**: Can be sent to external signing services or HSMs
        - **Signed**: Ready for submission to the network

        **Examples:**

        Unsigned transaction bytes (for external signing):
        ```python
        tx = TransferTransaction().add_hbar_transfer(...)
        tx.transaction_id = TransactionId.generate(account_id)
        tx.node_account_id = AccountId.from_string("0.0.3")
        tx.freeze()
        unsigned_bytes = tx.to_bytes()  # Can be sent to HSM for signing
        ```

        Signed transaction bytes (ready for submission):
        ```python
        tx.freeze()
        tx.sign(private_key)
        signed_bytes = tx.to_bytes()  # Ready to submit to network
        ```

        Returns:
            bytes: The protobuf-encoded transaction bytes.

        Raises:
            Exception: If the transaction has not been frozen yet.
        """
        self._require_frozen()
        
        # Get the transaction protobuf
        transaction_proto = self._to_proto()
        
        # Serialize to bytes
        return transaction_proto.SerializeToString()

    @staticmethod
    def from_bytes(transaction_bytes: bytes):
        """
        Deserializes a transaction from its protobuf-encoded byte representation.

        This method reconstructs a Transaction object from bytes that were previously
        created using to_bytes(). It supports all transaction types in the SDK.

        **What is restored:**
        - Transaction type and all transaction-specific fields
        - Common fields (transaction ID, node ID, memo, fee, etc.)
        - All signatures (if the transaction was signed)
        - Transaction state (frozen)

        **Examples:**

        Basic round-trip:
        ```python
        # Create and freeze a transaction
        tx = TransferTransaction().add_hbar_transfer(...)
        tx.freeze_with(client)
        tx.sign(private_key)

        # Serialize to bytes
        tx_bytes = tx.to_bytes()

        # Deserialize back to transaction
        restored_tx = Transaction.from_bytes(tx_bytes)

        # The restored transaction can be executed
        receipt = restored_tx.execute(client)
        ```

        External signing workflow:
        ```python
        # System A: Create unsigned transaction
        tx = TransferTransaction().add_hbar_transfer(...)
        tx.freeze_with(client)
        unsigned_bytes = tx.to_bytes()

        # Send unsigned_bytes to System B (HSM, hardware wallet)...

        # System B: Restore, sign, and serialize
        tx = Transaction.from_bytes(unsigned_bytes)
        tx.sign(hsm_private_key)
        signed_bytes = tx.to_bytes()

        # System A: Restore signed transaction and execute
        final_tx = Transaction.from_bytes(signed_bytes)
        receipt = final_tx.execute(client)
        ```

        Args:
            transaction_bytes (bytes): The protobuf-encoded transaction bytes.

        Returns:
            Transaction: A reconstructed transaction instance of the appropriate subclass.

        Raises:
            ValueError: If the bytes cannot be parsed or transaction type is unknown.
        """
        if not isinstance(transaction_bytes, bytes):
            raise ValueError("transaction_bytes must be bytes")

        if len(transaction_bytes) == 0:
            raise ValueError("transaction_bytes cannot be empty")

        try:
            transaction_proto = transaction_pb2.Transaction()
            transaction_proto.ParseFromString(transaction_bytes)
        except Exception as e:
            raise ValueError(f"Failed to parse transaction bytes: {e}")

        try:
            signed_transaction = transaction_contents_pb2.SignedTransaction()
            signed_transaction.ParseFromString(transaction_proto.signedTransactionBytes)
        except Exception as e:
            raise ValueError(f"Failed to parse signed transaction: {e}")

        try:
            transaction_body = transaction_pb2.TransactionBody()
            transaction_body.ParseFromString(signed_transaction.bodyBytes)
        except Exception as e:
            raise ValueError(f"Failed to parse transaction body: {e}")

        transaction_type = transaction_body.WhichOneof("data")

        if transaction_type is None:
            raise ValueError("Transaction body does not contain any transaction data")

        transaction_class = Transaction._get_transaction_class(transaction_type)

        if transaction_class is None:
            raise ValueError(f"Unknown transaction type: {transaction_type}")

        transaction_instance = transaction_class._from_protobuf(
            transaction_body, signed_transaction.bodyBytes, signed_transaction.sigMap
        )

        return transaction_instance

    @staticmethod
    def _get_transaction_class(transaction_type: str):
        """
        Maps a protobuf transaction type field name to the corresponding Python class.

        Args:
            transaction_type (str): The protobuf field name (e.g., "cryptoTransfer")

        Returns:
            type: The corresponding transaction class, or None if unknown
        """
        transaction_type_map = {
            "cryptoTransfer": "hiero_sdk_python.transaction.transfer_transaction.TransferTransaction",
            "contractCall": "hiero_sdk_python.contract.contract_execute_transaction.ContractExecuteTransaction",
            "contractCreateInstance": "hiero_sdk_python.contract.contract_create_transaction.ContractCreateTransaction",
            "contractUpdateInstance": "hiero_sdk_python.contract.contract_update_transaction.ContractUpdateTransaction",
            "contractDeleteInstance": "hiero_sdk_python.contract.contract_delete_transaction.ContractDeleteTransaction",
            "ethereumTransaction": "hiero_sdk_python.contract.ethereum_transaction.EthereumTransaction",
            "cryptoAddLiveHash": None,  # Not implemented in SDK
            "cryptoApproveAllowance": "hiero_sdk_python.account.account_allowance_approve_transaction.AccountAllowanceApproveTransaction",
            "cryptoDeleteAllowance": "hiero_sdk_python.account.account_allowance_delete_transaction.AccountAllowanceDeleteTransaction",
            "cryptoCreateAccount": "hiero_sdk_python.account.account_create_transaction.AccountCreateTransaction",
            "cryptoDelete": "hiero_sdk_python.account.account_delete_transaction.AccountDeleteTransaction",
            "cryptoDeleteLiveHash": None,  # Not implemented in SDK
            "cryptoUpdateAccount": "hiero_sdk_python.account.account_update_transaction.AccountUpdateTransaction",
            "fileAppend": "hiero_sdk_python.file.file_append_transaction.FileAppendTransaction",
            "fileCreate": "hiero_sdk_python.file.file_create_transaction.FileCreateTransaction",
            "fileDelete": "hiero_sdk_python.file.file_delete_transaction.FileDeleteTransaction",
            "fileUpdate": "hiero_sdk_python.file.file_update_transaction.FileUpdateTransaction",
            "systemDelete": None,  # Admin transaction
            "systemUndelete": None,  # Admin transaction
            "freeze": None,  # Admin transaction
            "consensusCreateTopic": "hiero_sdk_python.consensus.topic_create_transaction.TopicCreateTransaction",
            "consensusUpdateTopic": "hiero_sdk_python.consensus.topic_update_transaction.TopicUpdateTransaction",
            "consensusDeleteTopic": "hiero_sdk_python.consensus.topic_delete_transaction.TopicDeleteTransaction",
            "consensusSubmitMessage": "hiero_sdk_python.consensus.topic_message_submit_transaction.TopicMessageSubmitTransaction",
            "tokenCreation": "hiero_sdk_python.tokens.token_create_transaction.TokenCreateTransaction",
            "tokenFreeze": "hiero_sdk_python.tokens.token_freeze_transaction.TokenFreezeTransaction",
            "tokenUnfreeze": "hiero_sdk_python.tokens.token_unfreeze_transaction.TokenUnfreezeTransaction",
            "tokenGrantKyc": "hiero_sdk_python.tokens.token_grant_kyc_transaction.TokenGrantKycTransaction",
            "tokenRevokeKyc": "hiero_sdk_python.tokens.token_revoke_kyc_transaction.TokenRevokeKycTransaction",
            "tokenDeletion": "hiero_sdk_python.tokens.token_delete_transaction.TokenDeleteTransaction",
            "tokenUpdate": "hiero_sdk_python.tokens.token_update_transaction.TokenUpdateTransaction",
            "tokenMint": "hiero_sdk_python.tokens.token_mint_transaction.TokenMintTransaction",
            "tokenBurn": "hiero_sdk_python.tokens.token_burn_transaction.TokenBurnTransaction",
            "tokenWipe": "hiero_sdk_python.tokens.token_wipe_transaction.TokenWipeTransaction",
            "tokenAssociate": "hiero_sdk_python.tokens.token_associate_transaction.TokenAssociateTransaction",
            "tokenDissociate": "hiero_sdk_python.tokens.token_dissociate_transaction.TokenDissociateTransaction",
            "tokenPause": "hiero_sdk_python.tokens.token_pause_transaction.TokenPauseTransaction",
            "tokenUnpause": "hiero_sdk_python.tokens.token_pause_transaction.TokenUnpauseTransaction",
            "scheduleCreate": "hiero_sdk_python.schedule.schedule_create_transaction.ScheduleCreateTransaction",
            "scheduleDelete": "hiero_sdk_python.schedule.schedule_delete_transaction.ScheduleDeleteTransaction",
            "scheduleSign": "hiero_sdk_python.schedule.schedule_sign_transaction.ScheduleSignTransaction",
            "tokenFeeScheduleUpdate": None,  # Not commonly used
            "tokenUpdateNfts": "hiero_sdk_python.tokens.token_update_nfts_transaction.TokenUpdateNftsTransaction",
            "nodeCreate": "hiero_sdk_python.nodes.node_create_transaction.NodeCreateTransaction",
            "nodeUpdate": "hiero_sdk_python.nodes.node_update_transaction.NodeUpdateTransaction",
            "nodeDelete": "hiero_sdk_python.nodes.node_delete_transaction.NodeDeleteTransaction",
            "utilPrng": "hiero_sdk_python.prng_transaction.PrngTransaction",
            "tokenReject": "hiero_sdk_python.tokens.token_reject_transaction.TokenRejectTransaction",
            "tokenAirdrop": "hiero_sdk_python.tokens.token_airdrop_transaction.TokenAirdropTransaction",
            "tokenCancelAirdrop": "hiero_sdk_python.tokens.token_cancel_airdrop_transaction.TokenCancelAirdropTransaction",
        }

        class_path = transaction_type_map.get(transaction_type)

        if class_path is None:
            return None

        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import transaction class for type '{transaction_type}': {e}")

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        """
        Creates a transaction instance from protobuf components.

        This is an internal method that should be overridden by subclasses to restore
        transaction-specific fields.

        Args:
            transaction_body: The parsed TransactionBody protobuf
            body_bytes (bytes): The raw bytes of the transaction body
            sig_map: The SignatureMap protobuf containing signatures

        Returns:
            Transaction: A new transaction instance with all fields restored
        """
        transaction = cls()

        if transaction_body.HasField("transactionID"):
            transaction.transaction_id = TransactionId._from_proto(transaction_body.transactionID)

        if transaction_body.HasField("nodeAccountID"):
            transaction.node_account_id = AccountId._from_proto(transaction_body.nodeAccountID)

        transaction.transaction_fee = transaction_body.transactionFee
        transaction.transaction_valid_duration = transaction_body.transactionValidDuration.seconds
        transaction.generate_record = transaction_body.generateRecord
        transaction.memo = transaction_body.memo

        if transaction_body.max_custom_fees:
            from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
            transaction.custom_fee_limits = [
                CustomFeeLimit._from_proto(fee) for fee in transaction_body.max_custom_fees
            ]

        if transaction.node_account_id:
            transaction._transaction_body_bytes[transaction.node_account_id] = body_bytes

        if sig_map and sig_map.sigPair:
            transaction._signature_map[body_bytes] = sig_map

        return transaction
