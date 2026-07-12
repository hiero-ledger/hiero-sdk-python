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
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.chunked_transaction import ChunkedTransaction


if TYPE_CHECKING:
    from hiero_sdk_python.channels import _Channel
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

        if self.contents is None:
            chunk_contents = b""
        else:
            start_index = self._current_chunk_index * self.chunk_size
            end_index = min(start_index + self.chunk_size, len(self.contents))
            chunk_contents = self.contents[start_index:end_index]

        return file_append_pb2.FileAppendTransactionBody(
            fileID=self.file_id._to_proto() if self.file_id else None, contents=chunk_contents
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
