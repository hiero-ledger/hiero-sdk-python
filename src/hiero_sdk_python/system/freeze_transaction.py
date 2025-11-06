"""
FreezeTransaction class for freezing the network.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.freeze_pb2 import FreezeTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.system.freeze_type import FreezeType
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction


class FreezeTransaction(Transaction):
    """
    Represents a freeze transaction on the network.

    This transaction freezes the network with the specified parameters including
    start_time, file_id, file_hash, and freeze_type.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a freeze transaction.
    """

    def __init__(
        self,
        start_time: Optional[Timestamp] = None,
        file_id: Optional[FileId] = None,
        file_hash: Optional[bytes] = None,
        freeze_type: Optional[FreezeType] = None,
    ):
        """
        Initializes a new FreezeTransaction instance with the specified parameters.

        Args:
            start_time (Optional[Timestamp]): The start time for the freeze.
            file_id (Optional[FileId]): The file ID containing the upgrade data.
            file_hash (Optional[bytes]): Hash of the file for verification.
            freeze_type (Optional[FreezeType]): The type of freeze to perform.
        """
        super().__init__()
        self.start_time: Optional[Timestamp] = start_time
        self.file_id: Optional[FileId] = file_id
        self.file_hash: Optional[bytes] = file_hash
        self.freeze_type: Optional[FreezeType] = freeze_type

    def set_start_time(self, start_time: Optional[Timestamp]) -> "FreezeTransaction":
        """
        Sets the start time for this freeze transaction.

        Args:
            start_time (Optional[Timestamp]): The start time for the freeze.

        Returns:
            FreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.start_time = start_time
        return self

    def set_file_id(self, file_id: Optional[FileId]) -> "FreezeTransaction":
        """
        Sets the file ID for this freeze transaction.

        Args:
            file_id (Optional[FileId]): The file ID containing the upgrade data.

        Returns:
            FreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_id = file_id
        return self

    def set_file_hash(self, file_hash: Optional[bytes]) -> "FreezeTransaction":
        """
        Sets the file hash for this freeze transaction.

        Args:
            file_hash (Optional[bytes]): Hash of the file for verification.

        Returns:
            FreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_hash = file_hash
        return self

    def set_freeze_type(self, freeze_type: Optional[FreezeType]) -> "FreezeTransaction":
        """
        Sets the freeze type for this freeze transaction.

        Args:
            freeze_type (Optional[FreezeType]): The type of freeze to perform.

        Returns:
            FreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.freeze_type = freeze_type
        return self

    def _build_proto_body(self) -> FreezeTransactionBody:
        """
        Returns the protobuf body for the freeze transaction.

        Returns:
            FreezeTransactionBody: The protobuf body for this transaction.
        """
        return FreezeTransactionBody(
            start_time=self.start_time._to_protobuf() if self.start_time else None,
            update_file=self.file_id._to_proto() if self.file_id else None,
            file_hash=self.file_hash,
            freeze_type=self.freeze_type._to_proto() if self.freeze_type else None,
        )

    def build_transaction_body(self) -> TransactionBody:
        """
        Builds the transaction body for this freeze transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        freeze_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.freeze.CopyFrom(freeze_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this freeze transaction.

        Returns:
            SchedulableTransactionBody: The schedulable transaction body.
        """
        freeze_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.freeze.CopyFrom(freeze_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the freeze transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to freeze the network.
        """
        return _Method(transaction_func=channel.freeze.freeze, query_func=None)
