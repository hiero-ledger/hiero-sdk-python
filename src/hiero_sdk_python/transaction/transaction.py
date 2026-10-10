from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Literal, overload

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.signer import Signer, _sign_to_signature_pair
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.executable import _Executable, _ExecutionState
from hiero_sdk_python.hapi.sdk.transaction_list_pb2 import TransactionList
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2, transaction_contents_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import SchedulableTransactionBody
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.lockable_list import _LockableList
from hiero_sdk_python.query.fee_estimate_query import FeeEstimateQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from hiero_sdk_python.utils.key_utils import key_to_proto


if TYPE_CHECKING:
    from hiero_sdk_python.crypto.private_key import PrivateKey
    from hiero_sdk_python.crypto.public_key import PublicKey
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
        """Initializes a new Transaction instance with default values."""
        super().__init__()

        self._transaction_ids = _LockableList[TransactionId]()
        self._transaction_fee: int | None = None
        self.transaction_valid_duration = 120
        self.generate_record = False
        self._high_volume = False
        self.memo = ""
        self.custom_fee_limits: list[CustomFeeLimit] = []
        # Maps TransactionId -> {AccountId: body_bytes} to prevent INVALID_NODE_ACCOUNT during node retries.
        self._transaction_body_bytes: dict[TransactionId, dict[AccountId, bytes]] = {}

        # Maps transaction body bytes to their associated signatures
        # This allows us to maintain the signatures for each unique transaction
        # and ensures that the correct signatures are used when submitting transactions
        self._signature_map: dict[bytes, basic_types_pb2.SignatureMap] = {}
        # Signers registered through sign_with(), kept so rebuilt bodies can be re-signed
        self._signers: list[tuple[PublicKey, Signer]] = []
        # changed from int: 2_000_000 to Hbar: 2
        self._default_transaction_fee = Hbar(2)
        self.operator_account_id = None
        self.batch_key: Key | None = None

    def _make_request(self):
        """
        Implements the Executable._make_request method to build the transaction request.

        This method simply converts the transaction to its protobuf representation
        using the _to_proto method.

        Returns:
            Transaction: The protobuf transaction message ready to be sent
        """
        return self._to_proto()

    def _map_response(self, response, node_id, proto_request):  # noqa: ARG002
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
            raise TypeError(f"Expected Transaction but got {type(proto_request)}")

        hash_obj = hashlib.sha384()
        hash_obj.update(proto_request.signedTransactionBytes)
        tx_hash = hash_obj.digest()
        transaction_response = TransactionResponse()
        transaction_response.transaction_id = self._transaction_ids.current
        transaction_response.node_id = node_id
        transaction_response.hash = tx_hash
        transaction_response._transaction_node_ids = self._node_account_ids.get_list()

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
            ResponseCode.INVALID_NODE_ACCOUNT,
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
        tx_id = self._transaction_ids.current

        return PrecheckError(error_code, tx_id)

    def sign(self, private_key: PrivateKey) -> Transaction:
        """
        Signs the transaction using the provided private key.

        Args:
            private_key (PrivateKey): The private key to sign the transaction with.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If the transaction body has not been built.
        """
        return self.sign_with(private_key.public_key(), private_key.sign)

    def sign_with(self, public_key: PublicKey, signer: Signer) -> Transaction:
        """
        Signs the transaction with a signer callback instead of a private key.

        Use this when the key is held outside the process, e.g. in an HSM or KMS.
        The signer is called once for every transaction body (every chunk and every node),
        with the exact body bytes, and must return the raw signature.

        Signing again with a key that already signed every body is a no-op.
        If the signer raises, the transaction is left unchanged.

        Args:
            public_key (PublicKey): The public key matching the signer.
            signer (Signer): The signing callback.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If the transaction body has not been built.
            TypeError: If the signer is not callable or does not return bytes.
        """
        # We require the transaction to be frozen before signing
        self._require_frozen()

        if not callable(signer):
            raise TypeError("signer must be callable")

        public_key_bytes = public_key.to_bytes_raw()
        if self._has_signer(public_key_bytes) or self.is_signed_by(public_key):
            return self

        self._write_signature_pairs(self._collect_signature_pairs(public_key, signer))
        self._signers.append((public_key, signer))

        return self

    def sign_with_operator(self, client: Client) -> Transaction:
        """
        Signs the transaction with the client's operator.

        Freezes the transaction with the client first if it is not frozen yet.

        Args:
            client (Client): The client whose operator signs the transaction.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            ValueError: If the client has no operator.
        """
        operator = client.operator
        if operator is None:
            raise ValueError("Client must have an operator to sign with the operator.")

        if not self._transaction_body_bytes:
            self.freeze_with(client)

        return self.sign_with(operator.public_key, operator.signer)

    def _apply_signers(self) -> None:
        """Re-signs every body that lacks a signature from a registered signer, e.g. after a rebuild."""
        pending = []
        for public_key, signer in self._signers:
            pending.extend(self._collect_signature_pairs(public_key, signer))

        self._write_signature_pairs(pending)

    def _collect_signature_pairs(
        self, public_key: PublicKey, signer: Signer
    ) -> list[tuple[bytes, basic_types_pb2.SignaturePair]]:
        """
        Signs every body not yet signed by public_key, without touching the signature map.

        We sign the bodies for each node in case we need to switch nodes during execution.
        """
        public_key_bytes = public_key.to_bytes_raw()

        return [
            (body_bytes, _sign_to_signature_pair(public_key, signer, body_bytes))
            for node_bytes_map in self._transaction_body_bytes.values()
            for body_bytes in node_bytes_map.values()
            if not self._is_body_signed_by(body_bytes, public_key_bytes)
        ]

    def _write_signature_pairs(self, signature_pairs: list[tuple[bytes, basic_types_pb2.SignaturePair]]) -> None:
        """Adds collected signature pairs to the signature map of their body."""
        for body_bytes, sig_pair in signature_pairs:
            self._signature_map.setdefault(body_bytes, basic_types_pb2.SignatureMap()).sigPair.append(sig_pair)

    def _has_signer(self, public_key_bytes: bytes) -> bool:
        """Checks if a signer for the given raw public key is registered."""
        return any(public_key.to_bytes_raw() == public_key_bytes for public_key, _ in self._signers)

    def _is_body_signed_by(self, body_bytes: bytes, public_key_bytes: bytes) -> bool:
        """Checks if the signature map of a body contains a signature for the given raw public key."""
        sig_map = self._signature_map.get(body_bytes)
        return sig_map is not None and any(sig_pair.pubKeyPrefix == public_key_bytes for sig_pair in sig_map.sigPair)

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
        current_tx_id = self._transaction_ids.current
        current_node_id = self._node_account_ids.current

        node_bodies = self._transaction_body_bytes.get(current_tx_id)
        if node_bodies is None:
            raise ValueError(f"No transaction bodies built for Transaction ID {current_tx_id}")

        body_bytes = node_bodies.get(current_node_id)
        if body_bytes is None:
            raise ValueError(f"No transaction body found for node {current_node_id}")

        # Get signature map, or create empty one if transaction is not signed
        sig_map = self._signature_map.get(body_bytes)
        if sig_map is None:
            sig_map = basic_types_pb2.SignatureMap()

        signed_transaction = transaction_contents_pb2.SignedTransaction(bodyBytes=body_bytes, sigMap=sig_map)

        return transaction_pb2.Transaction(signedTransactionBytes=signed_transaction.SerializeToString())

    def _resolve_transaction_id(self, client: Client):
        if not self._transaction_ids.is_empty:
            return

        if client is not None:
            operator_account_id = client.operator_account_id
            if operator_account_id is not None:
                self._transaction_ids.set_list([client.generate_transaction_id()])
            else:
                raise ValueError("Client must have an operator_account or transactionId must be set.")
        else:
            raise ValueError(
                "Transaction ID must be set before freezing. Use freeze_with(client) or set_transaction_id()."
            )

    def _resolve_node_ids(self, client: Client):
        if self._node_account_ids.is_empty and client is None:
            raise ValueError(
                "Node account ID must be set before freezing. Use freeze_with(client) or manually set node_account_ids."
            )

        # For Inner Transaction of batch transaction node_account_id=0.0.0
        if self.batch_key:
            self._node_account_ids.set_list([AccountId(0, 0, 0)])

        # If not nodes set manually use the all network nodes available in client
        if self._node_account_ids.is_empty:
            self._node_account_ids.set_list([node._account_id for node in client.network.nodes])

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
        return self.freeze_with(None)

    def freeze_with(self, client: Client):
        """
        Freezes the transaction by building the transaction body and setting necessary IDs.

        Args:
            client (Client): The client instance to use for setting defaults.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            Exception: If required IDs are not set.
        """
        if self._is_frozen:
            return self

        # Resolve transaction_id and node_accountids to be set when using freeze()
        self._resolve_transaction_id(client)
        self._resolve_node_ids(client)

        required_chunks = self.get_required_chunks()
        self._generate_transaction_ids(self._transaction_ids.get(0), required_chunks)

        # We iterate through every node in the node_account_id list and
        # For each node_account_id build the transaction body
        # This allows the transaction to be submitted to the given node in the network
        self._node_account_ids.set_lock(True)
        self._transaction_ids.set_lock(True)

        for index, transaction_id in enumerate(self._transaction_ids):
            node_transaction_bodies = {}

            self._set_current_chunk_index(index)
            transaction_body = self.build_transaction_body()

            for node_account_id in self._node_account_ids.get_list():
                transaction_body.transactionID.CopyFrom(transaction_id._to_proto())
                transaction_body.nodeAccountID.CopyFrom(node_account_id._to_proto())
                node_transaction_bodies[node_account_id] = transaction_body.SerializeToString()

            self._transaction_body_bytes[transaction_id] = node_transaction_bodies

        self._set_current_chunk_index(None)

        return self

    def _generate_transaction_ids(self, initial_id: TransactionId, count: int) -> None:
        """Generate all transaction_id for require chunks."""
        self._transaction_ids.clear()

        if count == 1:
            self._transaction_ids.set_list([initial_id])
            return

        transaction_id = initial_id
        for i in range(count):
            self._transaction_ids.append(transaction_id)

            next_nanos = initial_id.valid_start.nanos + (i + 1)
            next_valid_start = timestamp_pb2.Timestamp(
                seconds=initial_id.valid_start.seconds + next_nanos // 1_000_000_000,
                nanos=next_nanos % 1_000_000_000,
            )

            transaction_id = TransactionId(
                account_id=self._transaction_ids.get(0).account_id, valid_start=next_valid_start
            )

    def _set_current_chunk_index(self, index: int | None) -> None:
        """Helper to set the current chunk index before building the transaction body."""
        pass

    @overload
    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> TransactionReceipt: ...

    @overload
    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> TransactionResponse: ...

    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: bool = True,
        validate_status: bool = False,
    ) -> TransactionReceipt | TransactionResponse:
        """
        Executes the transaction on the Hedera network using the provided client.

        This function delegates the core logic to `_execute()` and `get_receipt()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.
            wait_for_receipt (bool, optional): Whether to wait for consensus and return the receipt.
                If False, the method returns a TransactionResponse immediately after submission.
            validate_status: (bool, optional):  Whether the query should automatically validate the transaction status.

        Returns:
            TransactionReceipt: If wait_for_receipt is True (default)
            TransactionResponse: If wait_for_receipt is False

        Raises:
            PrecheckError: If the transaction/query fails with a non-retryable error
            MaxAttemptsError: If the transaction/query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        from hiero_sdk_python.transaction.batch_transaction import BatchTransaction

        if self.batch_key and not isinstance(self, (BatchTransaction)):
            raise ValueError("Cannot execute batchified transaction outside of BatchTransaction.")

        if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, (int, float))):
            raise TypeError("timeout must be a int or float")

        if not isinstance(validate_status, bool):
            raise TypeError("validate_status must be a boolean")

        if not isinstance(wait_for_receipt, bool):
            raise TypeError("wait_for_receipt must be a boolean")

        if not isinstance(client, Client):
            raise TypeError("client must be an instance of Client")

        if not self._transaction_body_bytes:
            self.freeze_with(client)

        if self.operator_account_id is None:
            self.operator_account_id = client.operator_account_id

        # Sign with the operator only when it pays for the transaction
        operator = client.operator
        if operator is not None and self._transaction_ids.get(0).account_id == operator.account_id:
            self.sign_with(operator.public_key, operator.signer)

        # Call the _execute function from executable.py to handle the actual execution
        response: TransactionResponse = self._execute(client, timeout)

        response.validate_status = True
        response.transaction = self
        response.transaction_id = self._transaction_ids.current

        if wait_for_receipt:
            return response.get_receipt(client, timeout=timeout, validate_status=validate_status)

        return response

    def is_signed_by(self, public_key):
        """
        Checks if the transaction has been signed by the given public key.

        Args:
            public_key (PublicKey): The public key to check.

        Returns:
            bool: True if signed by the given public key, False otherwise.
        """
        public_key_bytes = public_key.to_bytes_raw()

        if not self._transaction_body_bytes:
            return False

        return all(
            self._is_body_signed_by(body_bytes, public_key_bytes)
            for node_transaction_bodies in self._transaction_body_bytes.values()
            for body_bytes in node_transaction_bodies.values()
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
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
        transaction_body = transaction_pb2.TransactionBody()

        fee = self._transaction_fee or self._default_transaction_fee
        if hasattr(fee, "to_tinybars"):
            transaction_body.transactionFee = int(fee.to_tinybars())
        else:
            transaction_body.transactionFee = int(fee)

        transaction_body.transactionValidDuration.seconds = self.transaction_valid_duration
        transaction_body.generateRecord = self.generate_record
        transaction_body.high_volume = self._high_volume
        transaction_body.memo = self.memo
        custom_fee_limits = [custom_fee._to_proto() for custom_fee in self.custom_fee_limits]
        transaction_body.max_custom_fees.extend(custom_fee_limits)

        if self.batch_key:
            transaction_body.batch_key.CopyFrom(key_to_proto(self.batch_key))

        return transaction_body

    def build_base_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the base scheduled transaction body including common fields.

        Returns:
            SchedulableTransactionBody:
                The protobuf SchedulableTransactionBody message with common fields set.
        """
        schedulable_body = SchedulableTransactionBody()

        fee = self._transaction_fee or self._default_transaction_fee
        if hasattr(fee, "to_tinybars"):
            schedulable_body.transactionFee = int(fee.to_tinybars())
        else:
            schedulable_body.transactionFee = int(fee)

        schedulable_body.memo = self.memo
        custom_fee_limits = [custom_fee._to_proto() for custom_fee in self.custom_fee_limits]
        schedulable_body.max_custom_fees.extend(custom_fee_limits)

        return schedulable_body

    def schedule(self) -> ScheduleCreateTransaction:
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
        if self._is_frozen:
            raise Exception("Transaction is immutable; it has been frozen.")

    def _require_frozen(self) -> None:
        """
        Ensures the transaction is frozen before allowing operations that require a frozen transaction.

        This method checks if the transaction has been frozen by verifying that transaction_body_bytes
        has been set.

        Raises:
            Exception: If the transaction has not been frozen yet.
        """
        if not self._is_frozen:
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

    def set_transaction_valid_duration(self, duration: int) -> Transaction:
        """
        Sets the valid duration for the transaction.

        Args:
            duration (int): The duration in seconds.

        Returns:
            Transaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if duration <= 0:
            raise ValueError("duration must be greater than 0")
        self.transaction_valid_duration = duration
        return self

    @property
    def transaction_id(self) -> TransactionId | None:
        if self._transaction_ids.is_empty:
            return None

        return self._transaction_ids.current

    @transaction_id.setter
    def transaction_id(self, transaction_id: TransactionId):
        self.set_transaction_id(transaction_id)

    def set_transaction_id(self, transaction_id: TransactionId):
        """
        Sets the transaction ID for the transaction.

        Args:
            transaction_id (TransactionId): The transaction ID to set.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            TypeError: If transaction_id is not a TransactionId instance.
            ValueError: If transaction_id does not contain an account ID or valid start time.
            Exception: If the transaction has already been frozen.
        """
        self._require_not_frozen()

        if transaction_id is None or not isinstance(transaction_id, TransactionId):
            raise TypeError("transaction_id must be of type TransactionId")

        if transaction_id.account_id is None or transaction_id.valid_start is None:
            raise ValueError("transaction_id must have account_id and a valid_start period")

        self._transaction_ids.set_list([transaction_id])
        return self

    # this will preserves original behavior
    @property
    def transaction_fee(self):
        """
        Set the maximum transaction fee for this transaction.
        """
        return self._transaction_fee

    @transaction_fee.setter
    def transaction_fee(self, fee: Hbar | int):
        """
        Set the maximum transaction fee for this transaction.
        """
        self._require_not_frozen()

        if isinstance(fee, Hbar):
            tinybars = fee.to_tinybars()
        elif isinstance(fee, bool) or not isinstance(fee, int):
            raise TypeError("fee must be of type Hbar or int")
        else:
            tinybars = fee

        if tinybars < 0:
            raise ValueError("fee must be greater than or equal to 0")

        self._transaction_fee = tinybars

    def to_bytes(self) -> bytes:
        """
        Serializes the frozen transaction into its protobuf-encoded byte representation.

        This method is equivalent to the Javascript SDK's transaction.toBytes() method.

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
            bytes: The serialized TransactionList as bytes.
        """
        transaction_list = TransactionList()

        if self._is_frozen:
            for node_body_bytes in self._transaction_body_bytes.values():
                for body_bytes in node_body_bytes.values():
                    transaction_list.transaction_list.append(self._build_transaction_from_body_bytes(body_bytes))

            return transaction_list.SerializeToString()

        transaction_body = self.build_transaction_body()

        if not self._transaction_ids.is_empty:
            transaction_body.transactionID.CopyFrom(self._transaction_ids.get(0)._to_proto())

        node_account_ids = self._node_account_ids.get_list() if not self._node_account_ids.is_empty else [None]

        for node_account_id in node_account_ids:
            if node_account_id is not None:
                transaction_body.nodeAccountID.CopyFrom(node_account_id._to_proto())

            transaction_list.transaction_list.append(
                self._build_transaction_from_body_bytes(transaction_body.SerializeToString())
            )

        return transaction_list.SerializeToString()

    def _build_transaction_from_body_bytes(self, body_bytes: bytes) -> transaction_pb2.Transaction:
        """
        Build a protobuf Transaction from serialized transaction body bytes.
        Unfrozen transactions contain the body directly in bodyBytes.
        Frozen transactions contain a SignedTransaction with the body and signature map.
        An empty signature map is included when the transaction has not been signed yet.

        Args:
            body_bytes: Serialized TransactionBody bytes.

        Returns:
            transaction_pb2.Transaction: The transaction protobuf.
        """
        if not self._is_frozen:
            return transaction_pb2.Transaction(bodyBytes=body_bytes)

        # for frozen transaction
        signed_transaction = transaction_contents_pb2.SignedTransaction(bodyBytes=body_bytes)
        signature_map = self._signature_map.get(body_bytes)

        if signature_map is not None:
            signed_transaction.sigMap.CopyFrom(signature_map)
        else:
            signed_transaction.sigMap.CopyFrom(basic_types_pb2.SignatureMap(sigPair=[]))

        return transaction_pb2.Transaction(signedTransactionBytes=signed_transaction.SerializeToString())

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
            ValueError: If the bytes are invalid, contain no transactions,
                or contain an unknown transaction type.
        """
        if not isinstance(transaction_bytes, bytes):
            raise ValueError("transaction_bytes must be bytes")
        if not transaction_bytes:
            raise ValueError("transaction_bytes cannot be empty")

        try:
            return Transaction._process_transaction_list_bytes(transaction_bytes)
        except Exception:
            try:
                # Backward compatibility
                return Transaction._process_single_transaction_bytes(transaction_bytes)
            except Exception as e:
                raise ValueError(f"Failed to parse transaction_bytes {e}") from e

    @staticmethod
    def _process_base_transaction(
        transaction_proto: transaction_pb2.Transaction,
    ) -> tuple[type[Transaction], transaction_pb2.TransactionBody, transaction_contents_pb2.SignedTransaction]:
        """Parses a serialized Transaction protobuf."""
        if not isinstance(transaction_proto, transaction_pb2.Transaction):
            raise TypeError("transaction_proto must be a transaction_pb2.Transaction")

        if transaction_proto.bodyBytes:
            signed_transaction = transaction_contents_pb2.SignedTransaction(bodyBytes=transaction_proto.bodyBytes)
            if transaction_proto.HasField("sigMap"):
                signed_transaction.sigMap.CopyFrom(transaction_proto.sigMap)

        elif transaction_proto.signedTransactionBytes:
            try:
                signed_transaction = transaction_contents_pb2.SignedTransaction()
                signed_transaction.ParseFromString(transaction_proto.signedTransactionBytes)
            except Exception as e:
                raise ValueError(f"Failed to parse signed transaction: {e}") from e

        else:
            raise ValueError("Transaction does not contain bodyBytes or signedTransactionBytes")

        try:
            transaction_body = transaction_pb2.TransactionBody()
            transaction_body.ParseFromString(signed_transaction.bodyBytes)
        except Exception as e:
            raise ValueError(f"Failed to parse transaction body: {e}") from e

        transaction_type = transaction_body.WhichOneof("data")
        if transaction_type is None:
            raise ValueError("Transaction body does not contain any transaction data")
        transaction_class = Transaction._get_transaction_class(transaction_type)

        if transaction_class is None:
            raise ValueError(f"Unknown transaction type: {transaction_type}")

        return transaction_class, transaction_body, signed_transaction

    # For backward compatiblity only
    @staticmethod
    def _process_single_transaction_bytes(transaction_bytes: bytes) -> Transaction:
        """Deserializes a single Transaction protobuf."""
        try:
            transaction_proto = transaction_pb2.Transaction()
            transaction_proto.ParseFromString(transaction_bytes)
        except Exception as e:
            raise ValueError(f"Failed to parse transaction bytes: {e}") from e

        transaction_class, transaction_body, signed_transaction = Transaction._process_base_transaction(
            transaction_proto
        )

        transaction = transaction_class._from_protobuf(transaction_body)

        Transaction._restore_signatures(
            transaction,
            transaction,
            signed_transaction,
        )

        Transaction._lock_restored_transaction(transaction)
        return transaction

    @staticmethod
    def _process_transaction_list_bytes(transaction_bytes: bytes) -> Transaction:
        """Deserializes a TransactionList protobuf."""
        try:
            transaction_list = TransactionList()
            transaction_list.ParseFromString(transaction_bytes)
        except Exception as e:
            raise ValueError(f"Failed to parse TransactionList: {e}") from e

        if not transaction_list.transaction_list:
            raise ValueError("TransactionList contains no transactions")

        restored_transaction: Transaction | None = None
        transaction_ids: list[Transaction] = []
        node_account_ids: list[AccountId] = []
        bodies: list[transaction_pb2.TransactionBody] = []

        for transaction_proto in transaction_list.transaction_list:
            transaction_class, transaction_body, signed_transaction = Transaction._process_base_transaction(
                transaction_proto
            )

            transaction = transaction_class._from_protobuf(transaction_body)

            if restored_transaction is None:
                restored_transaction = transaction
            elif type(transaction) is not type(restored_transaction):
                raise ValueError("TransactionList contains different transaction types")

            if transaction.transaction_id is not None:
                transaction_id = transaction.transaction_id

                if transaction_id not in transaction_ids:
                    transaction_ids.append(transaction_id)

            if not transaction._node_account_ids.is_empty:
                node_account_id = transaction._node_account_ids.get(0)

                if node_account_id not in node_account_ids:
                    node_account_ids.append(node_account_id)

            bodies.append(transaction_body)

            Transaction._restore_signatures(
                restored_transaction,
                transaction,
                signed_transaction,
            )

        if restored_transaction is None:
            raise ValueError("TransactionList contains no valid transactions")

        transaction_type = bodies[0].WhichOneof("data")

        Transaction._validate_transaction_bodies(
            transaction_type=transaction_type,
            transaction_ids=transaction_ids,
            node_ids=node_account_ids,
            bodies=bodies,
        )

        if transaction_ids:
            for transaction_id in transaction_ids:
                if transaction_id not in restored_transaction._transaction_ids.get_list():
                    restored_transaction._transaction_ids.append(transaction_id)

        if node_account_ids:
            restored_transaction._node_account_ids.clear()
            restored_transaction.set_node_account_ids(node_account_ids)

        Transaction._lock_restored_transaction(restored_transaction)
        return restored_transaction

    @staticmethod
    def _restore_signatures(restored_transaction: Transaction, transaction: Transaction, signed_transaction) -> None:
        """Restores signature maps and body bytes."""

        if not signed_transaction.HasField("sigMap"):
            return

        if signed_transaction.sigMap.sigPair:
            restored_transaction._signature_map[signed_transaction.bodyBytes] = signed_transaction.sigMap

        if not transaction._transaction_ids.is_empty and not transaction._node_account_ids.is_empty:
            tx_id = transaction._transaction_ids.get(0)

            restored_transaction._transaction_body_bytes.setdefault(tx_id, {})
            restored_transaction._transaction_body_bytes[tx_id][transaction._node_account_ids.get(0)] = (
                signed_transaction.bodyBytes
            )

    @staticmethod
    def _lock_restored_transaction(transaction: Transaction) -> None:
        """Lock transaction identifiers and node IDs after deserialization."""
        if not transaction._is_frozen:
            return

        transaction._transaction_ids.set_lock(True)
        transaction._node_account_ids.set_lock(True)

    @staticmethod
    def _validate_transaction_pairs(
        transaction_ids: list[TransactionId],
        node_ids: list[AccountId],
        bodies: list[transaction_pb2.TransactionBody],
    ) -> None:
        """
        Validate that each transaction-node pair occurs exactly once and are ordered.

        Raises:
            ValueError: If a pair is duplicated, missing, or out of order.
        """
        if not transaction_ids or not node_ids:
            return

        expected_pairs = [
            (
                transaction_id._to_proto().SerializeToString(),
                node_id._to_proto().SerializeToString(),
            )
            for transaction_id in transaction_ids
            for node_id in node_ids
        ]

        actual_pairs = []

        for body in bodies:
            if not body.HasField("transactionID") or not body.HasField("nodeAccountID"):
                raise ValueError("Failed to validate transaction bodies: transaction ID or node account ID is missing")

            actual_pairs.append(
                (
                    body.transactionID.SerializeToString(),
                    body.nodeAccountID.SerializeToString(),
                )
            )

        if len(actual_pairs) != len(set(actual_pairs)):
            raise ValueError("Failed to validate transaction bodies: duplicate transaction ID and node account ID pair")

        if actual_pairs != expected_pairs:
            raise ValueError(
                "Failed to validate transaction bodies: missing or incorrectly ordered transaction-node pairs"
            )

    @staticmethod
    def _validate_transaction_bodies(
        transaction_type: str,
        transaction_ids: list[TransactionId],
        node_ids: list[AccountId],
        bodies: list[transaction_pb2.TransactionBody],
    ) -> None:
        """
        Validate transaction body shape and consistency for serialize TransactionList.

        Raises:
            ValueError: If the transaction bodies have an invalid shape or
                inconsistent fields.
        """
        if not transaction_ids or not bodies:
            return

        transaction_count = len(transaction_ids)
        node_count = len(node_ids)
        group_size = node_count if node_count > 0 else 1

        is_chunk_transaction = transaction_type == "fileAppend" or transaction_type == "consensusSubmitMessage"
        has_invalid_transaction_count = not is_chunk_transaction and transaction_count != 1

        if node_count == 0:
            has_unexpected_body_count = len(bodies) != transaction_count

            if has_unexpected_body_count or has_invalid_transaction_count:
                raise ValueError("Failed to validate transaction bodies")

            return

        # `_transaction_body_bytes` maps each transaction ID to its node-specific body bytes: `transaction_id -> {node_id -> body_bytes}`.
        #
        # When serialized, these entries are flattened into a `TransactionList` ordered by transaction, then by node:
        # [tx1/node1, tx1/node2, tx1/node3, tx2/node1, tx2/node2, tx2/node3, ...]
        expected_body_count = transaction_count * group_size
        if len(bodies) != expected_body_count or has_invalid_transaction_count:
            raise ValueError("Failed to validate transaction bodies")

        # check for unique pairs and pair order
        Transaction._validate_transaction_pairs(transaction_ids, node_ids, bodies)

        ignored_fields = {"nodeAccountID"}
        for transaction_index in range(transaction_count):
            row_start = transaction_index * node_count
            reference_body = bodies[row_start]

            for node_index in range(1, node_count):
                if not Transaction._compare_transaction_bodies(
                    reference_body,
                    bodies[row_start + node_index],
                    ignored_fields,
                ):
                    raise ValueError("Failed to validate transaction bodies")

        if is_chunk_transaction:
            Transaction._validate_chunked_transaction_bodies(
                transaction_type,
                bodies,
                group_size,
            )

    @staticmethod
    def _validate_chunked_transaction_bodies(
        transaction_type: str, bodies: list[transaction_pb2.TransactionBody], group_size: int
    ) -> None:
        """
        Validate invariant fields shared across chunk groups.

        Raises:
            ValueError: If invariant fields differ between chunk groups.
        """
        ignored_fields = {"nodeAccountID", "transactionID"}

        if transaction_type == "fileAppend":
            ignored_fields.add("contents")
        elif transaction_type == "consensusSubmitMessage":
            ignored_fields.update({"message", "chunkInfo"})

        reference_body = bodies[0]

        for body_index in range(group_size, len(bodies), group_size):
            if not Transaction._compare_transaction_bodies(
                reference_body,
                bodies[body_index],
                ignored_fields,
            ):
                raise ValueError("Failed to validate transaction bodies")

    @staticmethod
    def _compare_transaction_bodies(
        first: transaction_pb2.TransactionBody,
        second: transaction_pb2.TransactionBody,
        ignored_fields: set[str],
    ) -> bool:
        """
        Compare two transaction bodies while ignoring selected fields.

        Returns:
            bool: True if the remaining fields are equal.
        """

        def get_fields(message) -> dict:
            fields = {}

            for field, value in message.ListFields():
                if field.name in ignored_fields:
                    continue

                if hasattr(value, "ListFields"):
                    fields[field.name] = get_fields(value)
                else:
                    fields[field.name] = value

            return fields

        return get_fields(first) == get_fields(second)

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
            "systemDelete": None,  # Admin transaction (Deprecated)
            "systemUndelete": None,  # Admin transaction (Deprecated)
            "freeze": "hiero_sdk_python.system.freeze_transaction.FreezeTransaction",
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
            "token_pause": "hiero_sdk_python.tokens.token_pause_transaction.TokenPauseTransaction",
            "token_unpause": "hiero_sdk_python.tokens.token_unpause_transaction.TokenUnpauseTransaction",
            "token_update_nfts": "hiero_sdk_python.tokens.token_update_nfts_transaction.TokenUpdateNftsTransaction",
            "util_prng": "hiero_sdk_python.prng_transaction.PrngTransaction",
            "scheduleCreate": "hiero_sdk_python.schedule.schedule_create_transaction.ScheduleCreateTransaction",
            "scheduleDelete": "hiero_sdk_python.schedule.schedule_delete_transaction.ScheduleDeleteTransaction",
            "scheduleSign": "hiero_sdk_python.schedule.schedule_sign_transaction.ScheduleSignTransaction",
            "token_fee_schedule_update": "hiero_sdk_python.tokens.token_fee_schedule_update_transaction.TokenFeeScheduleUpdateTransaction",
            "nodeCreate": "hiero_sdk_python.nodes.node_create_transaction.NodeCreateTransaction",
            "nodeUpdate": "hiero_sdk_python.nodes.node_update_transaction.NodeUpdateTransaction",
            "nodeDelete": "hiero_sdk_python.nodes.node_delete_transaction.NodeDeleteTransaction",
            "registeredNodeCreate": "hiero_sdk_python.nodes.registered_node_create_transaction.RegisteredNodeCreateTransaction",
            "registeredNodeUpdate": "hiero_sdk_python.nodes.registered_node_update_transaction.RegisteredNodeUpdateTransaction",
            "registeredNodeDelete": "hiero_sdk_python.nodes.registered_node_delete_transaction.RegisteredNodeDeleteTransaction",
            "tokenReject": "hiero_sdk_python.tokens.token_reject_transaction.TokenRejectTransaction",
            "tokenAirdrop": "hiero_sdk_python.tokens.token_airdrop_transaction.TokenAirdropTransaction",
            "tokenClaimAirdrop": "hiero_sdk_python.tokens.token_airdrop_claim.TokenClaimAirdropTransaction",
            "tokenCancelAirdrop": "hiero_sdk_python.tokens.token_airdrop_transaction_cancel.TokenCancelAirdropTransaction",
            "atomic_batch": "hiero_sdk_python.transaction.batch_transaction.BatchTransaction",
        }

        class_path = transaction_type_map.get(transaction_type)

        if class_path is None:
            return None

        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import transaction class for type '{transaction_type}': {e}") from e

    @classmethod
    def _from_protobuf(cls, transaction_body):
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
            transaction.set_transaction_id(TransactionId._from_proto(transaction_body.transactionID))

        if transaction_body.HasField("nodeAccountID"):
            transaction.set_node_account_ids([AccountId._from_proto(transaction_body.nodeAccountID)])

        transaction.transaction_fee = transaction_body.transactionFee
        transaction.transaction_valid_duration = transaction_body.transactionValidDuration.seconds
        transaction.generate_record = transaction_body.generateRecord
        transaction._high_volume = transaction_body.high_volume
        transaction.memo = transaction_body.memo

        if transaction_body.max_custom_fees:
            from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit

            transaction.custom_fee_limits = [
                CustomFeeLimit._from_proto(fee) for fee in transaction_body.max_custom_fees
            ]

        return transaction

    def set_batch_key(self, key: Key):
        """
        Set the batch key required for batch transaction.

        Args:
            batch_key (Key): Key to use as batch key (accepts both PrivateKey and PublicKey).

        Returns:
            Transaction: A reconstructed transaction instance of the appropriate subclass.
        """
        self._require_not_frozen()
        self.batch_key = key
        return self

    def set_high_volume(self, high_volume: bool) -> Transaction:
        """
        Enables or disables high-volume throttles for this transaction.

        When enabled, the transaction may use high-volume capacity with
        dynamic pricing as defined by HIP-1313.

        Args:
            high_volume (bool): Whether to enable high-volume throttles.

        Returns:
            Transaction: The current transaction instance for method chaining.

        Raises:
            TypeError: If high_volume is not a bool.
            Exception: If the transaction has already been frozen.
        """
        self._require_not_frozen()

        if not isinstance(high_volume, bool):
            raise TypeError("high_volume must be of type bool")

        self._high_volume = high_volume
        return self

    def batchify(self, client: Client, batch_key: Key):
        """
        Marks the current transaction as an inner (batched) transaction.

        Args:
            client (Client): The client instance to use for setting defaults.
            batch_key (Key): Key to use as batch key (accepts both PrivateKey and PublicKey).

        Returns:
            Transaction: A reconstructed transaction instance of the appropriate subclass.
        """
        self._require_not_frozen()
        self.set_batch_key(batch_key)
        self.freeze_with(client)
        self.sign_with_operator(client)
        return self

    def estimate_fee(self) -> FeeEstimateQuery:
        """
        Creates a FeeEstimateQuery for this transaction.

        Returns:
            FeeEstimateQuery: A query configured to estimate fees for this transaction.
        """

        query = FeeEstimateQuery()
        query.set_transaction(self)
        return query

    def get_required_chunks(self) -> int:
        """
        Returns the number of chunks required for the current message.

        Returns:
            int: Number of chunks required.
        """
        return 1

    @property
    def size(self) -> int:
        """Returns the total transaction size in bytes after protobuf encoding"""
        self._require_frozen()
        return self._make_request().ByteSize()

    @property
    def body_size(self) -> int:
        """Returns just the transaction body size in bytes after encoding"""
        self._require_frozen()
        transaction_body = transaction_pb2.TransactionBody()
        transaction_body.ParseFromString(
            self._transaction_body_bytes.get(self._transaction_ids.current).get(self._node_account_ids.current)
        )
        return transaction_body.ByteSize()

    @property
    def high_volume(self) -> bool:
        """
        Returns whether high-volume throttles are enabled for this transaction.

        Returns:
            bool: True if high-volume throttles are enabled.
        """
        return self._high_volume

    @property
    def _is_frozen(self) -> bool:
        """
        Check whether the transaction is frozen.

        Returns:
            bool: True if transaction has been frozen otherwise, False
        """
        return bool(self._transaction_body_bytes)
