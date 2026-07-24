from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal, TypeVar, overload

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse


T = TypeVar("T", bound="ChunkedTransaction")


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
        self._current_chunk_index: int | None = None
        self._total_chunks: int = 1
        self._initial_transaction_id: TransactionId | None = None

        # Chunk configuration (set by subclasses)
        self.chunk_size: int = 1024
        self.max_chunks: int = 20

    @abstractmethod
    def _build_proto_body(self: T):
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

    def set_chunk_size(self: T, chunk_size: int) -> T:
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

    def set_max_chunks(self: T, max_chunks: int) -> T:
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

    def _validate_chunking(self: T) -> None:
        """
        Validates that the transaction doesn't exceed the maximum number of chunks.

        Raises:
            ValueError: If the transaction exceeds the maximum number of chunks.
        """
        if self.max_chunks and self.get_required_chunks() > self.max_chunks:
            raise ValueError(
                f"Cannot execute ChunkedTransaction with more than {self.max_chunks} chunks. "
                f"Required: {self.get_required_chunks()} Increase limit with set_max_chunks()."
            )

    def freeze_with(self: T, client: Client) -> T:
        """
        Freezes the transaction by building transaction bodies for all chunks.

        For multi-chunk transactions, generates sequential TransactionIds with
        incremented timestamps to ensure proper chunk ordering.

        Args:
            client (Client): The client instance to use for setting defaults.

        Returns:
            ChunkedTransaction: This transaction instance for chaining.
        """
        self._validate_chunking()

        if self._transaction_body_bytes:
            return self

        self._resolve_transaction_id(client)
        self._resolve_node_ids(client)

        self._initial_transaction_id = self._transaction_ids[0]

        required_chunks = self.get_required_chunks()
        self._generate_transaction_ids(self._transaction_ids[0], required_chunks)

        for chunk in range(required_chunks):
            self._current_chunk_index = chunk
            self._current_transaction_id_index = chunk

            node_bytes = {}

            for node_account_id in self.node_account_ids:
                self._node_account_id = node_account_id

                transaction_body = self.build_transaction_body()
                transaction_body.transactionID.CopyFrom(self._transaction_ids[chunk]._to_proto())
                transaction_body.nodeAccountID.CopyFrom(node_account_id._to_proto())

                node_bytes[node_account_id] = transaction_body.SerializeToString()

            self._transaction_body_bytes[self._transaction_ids[chunk]] = node_bytes

        self._current_chunk_index = None
        self._current_transaction_id_index = 0

        return super().freeze_with(client)

    @overload
    def execute(
        self: T,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> TransactionReceipt: ...

    @overload
    def execute(
        self: T,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> TransactionResponse: ...

    def execute(
        self: T,
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
        self: T,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> list[TransactionReceipt]: ...

    @overload
    def execute_all(
        self: T,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> list[TransactionResponse]: ...

    def execute_all(
        self: T,
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

        if not self._transaction_body_bytes:
            self.freeze_with(client)

        # Single chunk transaction
        if len(self._transaction_ids) == 1:
            return [super().execute(client, timeout, wait_for_receipt, validate_status)]

        # Multi-chunk transaction - execute all chunks
        responses = []
        self._current_transaction_id_index = 0
        for index in range(len(self._transaction_ids)):
            self._current_transaction_id_index = index
            response = super().execute(client, timeout, wait_for_receipt, validate_status)
            responses.append(response)

        return responses

    @property
    def body_size_all_chunks(self: T) -> list[int]:
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

        original_chunk_index = self._current_chunk_index
        original_transaction_index = self._current_transaction_id_index

        try:
            for i, _ in enumerate(self._transaction_ids):
                self._current_transaction_id_index = i
                self._current_chunk_index = i
                sizes.append(self.body_size)
        finally:
            self._current_chunk_index = original_chunk_index
            self._current_transaction_id_index = original_transaction_index

        return sizes
