"""Transaction to update a file's contents, metadata, or keys on the network."""

from __future__ import annotations

# pylint: disable=no-name-in-module
from google.protobuf.wrappers_pb2 import StringValue

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.file_update_pb2 import FileUpdateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction


DEFAULT_TRANSACTION_FEE = Hbar(2).to_tinybars()


class FileUpdateTransaction(Transaction):
    """
    Represents a file update transaction on the network.

    This transaction updates the metadata and/or contents of a file. If a field is not set
    in the transaction body, the corresponding file attribute will be unchanged. This transaction
    must be signed by all the keys in the top level of a key list  of the file being updated.
    If the keys themselves are being updated, then the transaction must
    also be signed by all the new keys.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a file update transaction.
    """

    def __init__(
        self,
        file_id: FileId | None = None,
        keys: list[PublicKey] | None = None,
        contents: str | bytes | None = None,
        expiration_time: Timestamp | None = None,
        file_memo: str | None = None,
    ):  # pylint: [disable=too-many-arguments, disable=too-many-positional-arguments]
        """
        Initializes a new FileUpdateTransaction instance with the specified parameters.

        Args:
            file_id (FileId, optional): The ID of the file to update.
            keys (Optional[list[PublicKey]], optional): The new keys that are allowed to
            update/delete the file.
            contents (str | bytes, optional): The new contents of the file.
            Strings will be automatically encoded as UTF-8 bytes.
            expiration_time (Timestamp, optional): The new expiration time for the file.
            file_memo (str, optional): The new memo for the file.
        """
        super().__init__()
        self.file_id: FileId | None = file_id
        self.keys: list[PublicKey] | None = keys
        self.contents: bytes | None = self._encode_contents(contents)
        self.expiration_time: Timestamp | None = expiration_time
        self.file_memo: str | None = file_memo
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def _encode_contents(self, contents: str | bytes | None) -> bytes | None:
        """
        Helper method to encode string contents to UTF-8 bytes.

        Args:
            contents (str | bytes | None): The contents to encode.

        Returns:
            Optional[bytes]: The encoded contents or None if input is None.
        """
        if contents is None:
            return None
        if isinstance(contents, str):
            return contents.encode("utf-8")
        return contents

    def set_file_id(self, file_id: FileId | None) -> FileUpdateTransaction:
        """
        Sets the FileID to be updated.

        Args:
            file_id (FileId | None): The ID of the file to update.

        Returns:
            FileUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_id = file_id
        return self

    def set_keys(self, keys: list[PublicKey] | None | PublicKey) -> FileUpdateTransaction:
        """
        Sets the new list of keys that can modify or delete the file.

        Args:
            keys (list[PublicKey] | PublicKey | None): The new keys to set for the file.
                Can be a list of PublicKey objects, a single PublicKey, or None.

        Returns:
            FileUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        if isinstance(keys, PublicKey):
            self.keys = [keys]
        else:
            self.keys = keys
        return self

    def set_expiration_time(self, expiration_time: Timestamp | None) -> FileUpdateTransaction:
        """
        Sets the new expiry time for the file.

        Args:
            expiration_time (Timestamp | None): The new expiration time for the file.

        Returns:
            FileUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def set_contents(self, contents: bytes | str | None) -> FileUpdateTransaction:
        """
        Sets the new contents that should overwrite the file's current contents.

        Args:
            contents (bytes | str | None): The new contents for the file.
            Strings will be automatically encoded as UTF-8 bytes.

        Returns:
            FileUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contents = self._encode_contents(contents)
        return self

    def set_file_memo(self, file_memo: str | None) -> FileUpdateTransaction:
        """
        Sets the new memo to be associated with the file (UTF-8 encoding max 100 bytes).

        Args:
            file_memo (str | None): The new memo for the file.

        Returns:
            FileUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_memo = file_memo
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the file update transaction.

        Returns:
            FileUpdateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If file_id is not set.
        """
        if self.file_id is None:
            raise ValueError("Missing required FileID")

        return FileUpdateTransactionBody(
            fileID=self.file_id._to_proto(),
            keys=(KeyListProto(keys=[key._to_proto() for key in self.keys]) if self.keys else None),
            contents=self.contents if self.contents is not None else b"",
            expirationTime=(self.expiration_time._to_protobuf() if self.expiration_time else None),
            memo=(StringValue(value=self.file_memo) if self.file_memo is not None else None),
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this file update transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        file_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileUpdate.CopyFrom(file_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this file update transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        file_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.fileUpdate.CopyFrom(file_update_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the file update transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to update a file.
        """
        return _Method(transaction_func=channel.file.updateFile, query_func=None)
