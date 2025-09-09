"""
Transaction to delete a file on the network.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.file_delete_pb2 import FileDeleteTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction

DEFAULT_TRANSACTION_FEE = Hbar(2).to_tinybars()


class FileDeleteTransaction(Transaction):
    """
    Represents a file deletion transaction on the network.

    This transaction deletes a specified file, rendering it inactive.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a file deletion transaction.
    """

    def __init__(self, file_id: Optional[FileId] = None):
        """
        Initializes a new FileDeleteTransaction instance with optional file_id.

        Args:
            file_id (FileId, optional): The ID of the file to be deleted.
        """
        super().__init__()
        self.file_id = file_id
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def set_file_id(self, file_id: FileId) -> "FileDeleteTransaction":
        """
        Sets the ID of the file to be deleted.

        Args:
            file_id (FileId): The ID of the file to be deleted.

        Returns:
            FileDeleteTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.file_id = file_id
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the file delete transaction.

        Returns:
            FileDeleteTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If file_id is not set.
        """
        if self.file_id is None:
            raise ValueError("Missing required FileID")

        return FileDeleteTransactionBody(fileID=self.file_id._to_proto())

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for file deletion.

        Returns:
            TransactionBody: The protobuf transaction body containing the file deletion details.
        """
        file_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileDelete.CopyFrom(file_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this file delete transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        file_delete_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.fileDelete.CopyFrom(file_delete_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the file delete transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to delete a file.
        """
        return _Method(transaction_func=channel.file.deleteFile, query_func=None)
