"""
Represents a file append transaction on the network.

This transaction appends data to an existing file on the network. If a file has multiple keys,
all keys must sign to modify its contents.

The transaction supports chunking for large files, automatically breaking content into
smaller chunks if the content exceeds the chunk size limit.

Inherits from the base ChunkedTransaction class and implements the required methods
to build and execute a file append transaction.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import file_append_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import SchedulableTransactionBody
from hiero_sdk_python.hapi.services import file_append_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.chunked_transaction import ChunkedTransaction
from hiero_sdk_python.transaction.transaction import Transaction


if TYPE_CHECKING:
    from hiero_sdk_python.channels import _Channel
    from hiero_sdk_python.client.client import Client
    from hiero_sdk_python.executable import _Method


class FileAppendTransaction(ChunkedTransaction):
    """
    Represents a file append transaction on the network.

    This transaction appends data to an existing file on the network. If a file has multiple keys,
    all keys must sign to modify its contents.

    The transaction supports chunking for large files, automatically breaking content into
    smaller chunks if the content exceeds the chunk size limit.

    Inherits from the base ChunkedTransaction class and implements the required methods
    to build and execute a file append transaction.
    """

    def __init__(
        self,
        file_id: FileId | None = None,
        contents: str | bytes | None = None,
        max_chunks: int | None = None,
        chunk_size: int | None = None,
    ):
        super().__init__()
        self.file_id: FileId | None = file_id
        self.contents: bytes | None = self._encode_contents(contents)
        self.max_chunks: int = 20
        self.chunk_size: int = 4096
        self._default_transaction_fee = Hbar(5).to_tinybars()

        if max_chunks is not None:
            self.set_max_chunks(max_chunks)
        if chunk_size is not None:
            self.set_chunk_size(chunk_size)

        self._total_chunks = self._calculate_total_chunks()
        # Internal tracking for chunking
        self._current_chunk_index: int | None = None
        self._total_chunks: int = self._calculate_total_chunks()

    def _encode_contents(self, contents: str | bytes | None) -> bytes | None:
        """
        Helper method to encode string contents to UTF-8 bytes.

        Args:
            contents (Optional[str | bytes]): The contents to encode.

        Returns:
            Optional[bytes]: The encoded contents or None if input is None.
        """
        if contents is None:
            return None
        if isinstance(contents, str):
            return contents.encode("utf-8")
        return contents

    def _calculate_total_chunks(self) -> int:
        """
        Calculates the total number of chunks needed for the current contents.

        Returns:
            int: The total number of chunks needed.
        """
        if self.contents is None:
            return 1
        return math.ceil(len(self.contents) / self.chunk_size)

    def get_required_chunks(self) -> int:
        """
        Gets the number of chunks required for the current contents.

        Returns:
            int: The number of chunks required.
        """
        return self._calculate_total_chunks()

    def set_file_id(self, file_id: FileId) -> FileAppendTransaction:
        """
        Sets the file ID for this file append transaction.

        Args:
            file_id (FileId): The file ID to append to.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_id = file_id
        return self

    def set_contents(self, contents: str | bytes | None) -> FileAppendTransaction:
        """
        Sets the contents for this file append transaction.

        Args:
            contents (Optional[str | bytes]): The contents to append to the file.
                Strings will be automatically encoded as UTF-8 bytes.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contents = self._encode_contents(contents)
        self._total_chunks = self._calculate_total_chunks()
        return self

    def set_max_chunks(self, max_chunks: int) -> FileAppendTransaction:
        """
        Sets the maximum number of chunks allowed for this transaction.

        Args:
            max_chunks (int): The maximum number of chunks allowed.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        super().set_max_chunks(max_chunks)
        return self

    def set_chunk_size(self, chunk_size: int) -> FileAppendTransaction:
        """
        Sets the chunk size for this transaction.

        Args:
            chunk_size (int): The size of each chunk in bytes.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        super().set_chunk_size(chunk_size)
        return self

    def _build_proto_body(self) -> file_append_pb2.FileAppendTransactionBody:
        """
        Returns the protobuf body for the file append transaction.

        Returns:
            FileAppendTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If file_id is not set.
        """
        # Calculate the current chunk's content
        if self.file_id is None:
            raise ValueError("Missing required FileID")

        contents = self.contents if self.contents is not None else b""

        if self._current_chunk_index is not None:
            start_index = self._current_chunk_index * self.chunk_size
            end_index = min(start_index + self.chunk_size, len(contents))

            chunk_contents = contents[start_index:end_index]
            return file_append_pb2.FileAppendTransactionBody(
                fileID=self.file_id._to_proto() if self.file_id else None, contents=chunk_contents
            )
        return file_append_pb2.FileAppendTransactionBody(
            fileID=self.file_id._to_proto() if self.file_id else None, contents=contents
        )

    def build_transaction_body(self) -> Any:
        """
        Builds the transaction body for this file append transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        file_append_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileAppend.CopyFrom(file_append_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this file append transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        file_append_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.fileAppend.CopyFrom(file_append_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the file append transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to append to a file.
        """
        from hiero_sdk_python.executable import _Method

        return _Method(transaction_func=channel.file.appendContent, query_func=None)

    def _from_proto(self, proto: file_append_pb2.FileAppendTransactionBody) -> FileAppendTransaction:
        """
        Initializes a new FileAppendTransaction instance from a protobuf object.

        Args:
            proto: The protobuf object to initialize from.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        self.file_id = FileId._from_proto(proto.fileID) if proto.fileID else None
        self.contents = proto.contents
        self._total_chunks = self._calculate_total_chunks()
        return self

    def _validate_chunking(self) -> None:
        """
        Validates that the transaction doesn't exceed the maximum number of chunks.

        Raises:
            ValueError: If the transaction exceeds the maximum number of chunks.
        """
        if self.max_chunks and self.get_required_chunks() > self.max_chunks:
            raise ValueError(
                f"Cannot execute FileAppendTransaction with more than {self.max_chunks} chunks. "
                f"Required: {self.get_required_chunks()}"
            )

    def freeze_with(self, client: Client) -> FileAppendTransaction:
        """
        Freezes the transaction by building the transaction body and setting necessary IDs.

        For multi-chunk transactions, this method generates multiple transaction IDs
        with incremented timestamps based on the chunk interval.

        Args:
            client (Client): The client instance to use for setting defaults.

        Returns:
            FileAppendTransaction: The current transaction instance for method chaining.
        """
        if self._transaction_body_bytes:
            return self

        self._resolve_transaction_id(client)
        self._resolve_node_ids(client)

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
        Executes the file append transaction.

        For multi-chunk transactions, this method will execute all chunks sequentially and return first response.

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.
            wait_for_receipt (bool, optional): Whether to wait for consensus and return the receipt.
                If False, the method returns a TransactionResponse immediately after submission.
            validate_status: (bool):  Whether the query should automatically validate the transaction status (default False).

        Returns:
            TransactionReceipt: If wait_for_receipt is True (default)
            TransactionResponse: If wait_for_receipt is False
        """
        # Return the first response (as per JavaScript implementation)
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
        Executes the file append transaction.

        This method will execute all chunks sequentially and return list of response for each chunked

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.
            wait_for_receipt (bool, optional): Whether to wait for consensus and return the receipt.
                If False, the method returns a TransactionResponse immediately after submission.
            validate_status: (bool):  Whether the query should automatically validate the transaction status (default False).

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
    def body_size_all_chunks(self) -> list[int]:
        """Returns an array of body sizes for transactions with multiple chunks."""
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

    @classmethod
    def _from_protobuf(cls, transaction_body):
        transaction = super()._from_protobuf(transaction_body)
        if transaction_body.HasField("fileAppend"):
            transaction._from_proto(transaction_body.fileAppend)
        return transaction
