from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, overload

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse


if TYPE_CHECKING:
    pass


class ChunkedTransaction(Transaction, ABC):
    """
    Abstract base class for transactions that support chunking.

    Centralizes common chunking logic for transactions like TopicMessageSubmitTransaction
    and FileAppendTransaction that need to split large content into multiple chunks.

    Subclasses must implement:
    - get_required_chunks(): Calculate the number of chunks needed
    - _build_proto_body(): Build the protobuf body for the current chunk
    """

    def __init__(self) -> None:
        """Initializes a new ChunkedTransaction instance."""
        super().__init__()

        # Chunking state
        self._current_chunk_index: int = 0
        self._total_chunks: int = 1
        self._initial_transaction_id: TransactionId | None = None
        self._transaction_ids: list[TransactionId] = []
        self._signing_keys: list[PrivateKey] = []

        # Chunk configuration (set by subclasses)
        self.chunk_size: int = 1024
        self.max_chunks: int = 20

    @abstractmethod
    def get_required_chunks(self) -> int:
        """
        Returns the number of chunks required for the current content.

        Subclasses must implement this based on their content type.

        Returns:
            int: Number of chunks required.
        """
        pass

    @abstractmethod
    def _build_proto_body(self):
        """
        Builds the protobuf body for the current chunk.

        This method is called during freeze_with() and execute() for each chunk.
        Subclasses must implement this to extract the appropriate chunk content
        and build the transaction-specific body.

        Returns:
            The transaction-specific protobuf body (e.g., ConsensusSubmitMessageTransactionBody)

        Raises:
            ValueError: If required fields are missing.
        """
        pass

    def set_chunk_size(self, chunk_size: int) -> ChunkedTransaction:
        """
        Sets the chunk size for this transaction.

        Args:
            chunk_size (int): The size of each chunk in bytes.

        Returns:
            ChunkedTransaction: This transaction instance for chaining.

        Raises:
            ValueError: If chunk_size is not positive.
        """
        self._require_not_frozen()
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self.chunk_size = chunk_size
        self._total_chunks = self.get_required_chunks()
        return self

    def set_max_chunks(self, max_chunks: int) -> ChunkedTransaction:
        """
        Sets the maximum number of chunks allowed.

        Args:
            max_chunks (int): The maximum number of chunks allowed.

        Returns:
            ChunkedTransaction: This transaction instance for chaining.

        Raises:
            ValueError: If max_chunks is not positive.
        """
        self._require_not_frozen()
        if max_chunks <= 0:
            raise ValueError("max_chunks must be positive")

        self.max_chunks = max_chunks
        return self

    def _validate_chunking(self) -> int:
        """
        Validates that the required chunks don't exceed max_chunks.

        Raises:
            ValueError: If required chunks exceed max_chunks.
        """
        required = self.get_required_chunks()
        if required < 1:
            raise ValueError("Transaction must require at least one chunk")
        self._total_chunks = required

        if self.max_chunks and required > self.max_chunks:
            raise ValueError(
                f"Message requires {required} chunks but max_chunks={self.max_chunks}. "
                f"Increase limit with set_max_chunks()."
            )
        return required

    def freeze_with(self, client: Client) -> ChunkedTransaction:
        """
        Freezes the transaction by building transaction bodies for all chunks.

        For multi-chunk transactions, generates sequential TransactionIds with
        incremented timestamps to ensure proper chunk ordering.

        Args:
            client (Client): The client instance to use for setting defaults.

        Returns:
            ChunkedTransaction: This transaction instance for chaining.
        """
        if self._transaction_body_bytes:
            return self

        self._validate_chunking()
        self._resolve_transaction_id(client)

        if self.transaction_id is None or self.transaction_id.valid_start is None:
            raise ValueError("Transaction ID with valid_start must be set before freezing chunked transaction.")

        # Generate transaction IDs for all chunks if not already done
        if not self._transaction_ids:
            base_timestamp = self.transaction_id.valid_start

            for i in range(self.get_required_chunks()):
                if i == 0:
                    # First chunk uses the original transaction ID
                    if self._initial_transaction_id is None:
                        self._initial_transaction_id = self.transaction_id

                    chunk_transaction_id = self.transaction_id
                else:
                    # Subsequent chunks get incremented timestamps
                    # Add i nanoseconds to space out chunks
                    next_nanos = base_timestamp.nanos + i

                    chunk_valid_start = timestamp_pb2.Timestamp(
                        seconds=base_timestamp.seconds + next_nanos // 1_000_000_000, nanos=next_nanos % 1_000_000_000
                    )
                    chunk_transaction_id = TransactionId(
                        account_id=self.transaction_id.account_id, valid_start=chunk_valid_start
                    )

                self._transaction_ids.append(chunk_transaction_id)

        return super().freeze_with(client)

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
        Executes the chunked transaction.

        For multi-chunk transactions, executes all chunks sequentially and returns
        the first response. Single-chunk transactions are executed normally.

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds).
            wait_for_receipt (bool, optional): Whether to wait for consensus and return receipt.
            validate_status: (bool): Whether to automatically validate the transaction status.

        Returns:
            TransactionReceipt: If wait_for_receipt is True (default)
            TransactionResponse: If wait_for_receipt is False
        """
        # Return the first response as per existing implementations
        return self.execute_all(client, timeout, wait_for_receipt, validate_status)[0]

    @overload
    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> list[TransactionReceipt]: ...

    @overload
    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> list[TransactionResponse]: ...

    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: bool = True,
        validate_status: bool = False,
    ) -> list[TransactionReceipt] | list[TransactionResponse]:
        """
        Executes all chunks of the transaction sequentially.

        Returns a list of responses for each chunk executed.

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds).
            wait_for_receipt (bool, optional): Whether to wait for consensus and return receipts.
            validate_status: (bool): Whether to automatically validate transaction statuses.

        Returns:
            List[TransactionReceipt]: If wait_for_receipt is True (default)
            List[TransactionResponse]: If wait_for_receipt is False
        """
        self._validate_chunking()

        required_chunks = self.get_required_chunks()

        if required_chunks == 1:
            return [
                super().execute(
                    client,
                    timeout=timeout,
                    wait_for_receipt=wait_for_receipt,
                    validate_status=validate_status,
                )
            ]

        # Ensure the initial transaction ID and chunk transaction IDs exist.
        if not self._transaction_ids:
            self.freeze_with(client)

        responses = []

        for chunk_index in range(required_chunks):
            self._current_chunk_index = chunk_index

            if chunk_index < len(self._transaction_ids):
                self.transaction_id = self._transaction_ids[chunk_index]

            # Clear the frozen state to rebuild the body for this chunk.
            self._transaction_body_bytes.clear()
            self._signature_map.clear()

            self.freeze_with(client)

            for signing_key in self._signing_keys:
                super().sign(signing_key)

            response = super().execute(
                client,
                timeout=timeout,
                wait_for_receipt=wait_for_receipt,
                validate_status=validate_status,
            )
            responses.append(response)

        return responses

    def sign(self, private_key: PrivateKey) -> ChunkedTransaction:
        """
        Signs the transaction using the provided private key.

        For multi-chunk transactions, stores the signing key for later use when
        executing all chunks.

        Args:
            private_key (PrivateKey): The private key to sign with.

        Returns:
            ChunkedTransaction: This transaction instance for chaining.
        """
        super().sign(private_key)
        # Store the signing key for multi-chunk execution only after signing succeeds.
        if private_key not in self._signing_keys:
            self._signing_keys.append(private_key)
        return self

    @property
    def body_size_all_chunks(self) -> list[int]:
        """
        Returns an array of body sizes for each chunk in the transaction.

        Useful for estimating the total fee when dealing with multi-chunk transactions.

        Returns:
            list[int]: List of body sizes in bytes for each chunk.

        Raises:
            Exception: If the transaction is not frozen.
        """
        self._require_frozen()
        sizes = []

        original_index = self._current_chunk_index
        original_transaction_id = self.transaction_id

        try:
            for i, transaction_id in enumerate(self._transaction_ids):
                self._current_chunk_index = i
                self.transaction_id = transaction_id

                sizes.append(self.body_size)
        finally:
            self._current_chunk_index = original_index
            self.transaction_id = original_transaction_id

        return sizes
