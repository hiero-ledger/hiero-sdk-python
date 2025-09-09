import time
from typing import Optional
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import file_create_pb2
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class FileCreateTransaction(Transaction):
    """
    Represents a file create transaction on the network.
    
    This transaction creates a new file on the network with the specified keys, contents,
    expiration time and memo.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a file create transaction.
    """
    
    # 90 days in seconds is the default expiration time
    DEFAULT_EXPIRY_SECONDS = 90 * 24 * 60 * 60  # 7776000
    
    def __init__(self, keys: Optional[list[PublicKey]] = None, contents: Optional[str | bytes] = None, expiration_time: Optional[Timestamp] = None, file_memo: Optional[str] = None):
        """
        Initializes a new FileCreateTransaction instance with the specified parameters.

        Args:
            keys (Optional[list[PublicKey]], optional): The keys that are allowed to update/delete the file.
            contents (Optional[str | bytes], optional): The contents of the file to create. Strings will be automatically encoded as UTF-8 bytes.
            expiration_time (Optional[Timestamp], optional): The time at which the file should expire.
            file_memo (Optional[str], optional): A memo to include with the file.
        """
        super().__init__()
        self.keys: Optional[list[PublicKey]] = keys or []
        self.contents: Optional[bytes] = self._encode_contents(contents)
        self.expiration_time: Optional[Timestamp] = expiration_time if expiration_time else Timestamp(int(time.time()) + self.DEFAULT_EXPIRY_SECONDS, 0)
        self.file_memo: Optional[str] = file_memo
        self._default_transaction_fee = Hbar(5).to_tinybars()

    def _encode_contents(self, contents: Optional[str | bytes]) -> Optional[bytes]:
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
            return contents.encode('utf-8')
        return contents

    def set_keys(self, keys: Optional[list[PublicKey]] | PublicKey) -> 'FileCreateTransaction':
        """
        Sets the keys for this file create transaction.

        Args:
            keys (Optional[list[PublicKey]] | PublicKey): The keys to set for the file. Can be a list of PublicKey objects or None.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        if isinstance(keys, PublicKey):
            self.keys = [keys]
        else:
            self.keys = keys or []
        return self

    def set_contents(self, contents: Optional[str | bytes]) -> 'FileCreateTransaction':
        """
        Sets the contents for this file create transaction.

        Args:
            contents (Optional[str | bytes]): The contents of the file to create. Strings will be automatically encoded as UTF-8 bytes.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contents = self._encode_contents(contents)
        return self

    def set_expiration_time(self, expiration_time: Optional[Timestamp]) -> 'FileCreateTransaction':
        """
        Sets the expiration time for this file create transaction.

        Args:
            expiration_time (Optional[Timestamp]): The expiration time for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self
    
    def set_file_memo(self, file_memo: Optional[str]) -> 'FileCreateTransaction':
        """
        Sets the memo for this file create transaction.

        Args:
            file_memo (Optional[str]): The memo to set for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_memo = file_memo
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the file create transaction.

        Returns:
            FileCreateTransactionBody: The protobuf body for this transaction.
        """
        return file_create_pb2.FileCreateTransactionBody(
            keys=KeyListProto(keys=[key._to_proto() for key in self.keys or []]),
            contents=self.contents if self.contents is not None else b'',
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            memo=self.file_memo if self.file_memo is not None else ''
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this file create transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        file_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileCreate.CopyFrom(file_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this file create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        file_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.fileCreate.CopyFrom(file_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the file create transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to create a file.
        """
        return _Method(
            transaction_func=channel.file.createFile,
            query_func=None
        )
    
    def _from_proto(self, proto: file_create_pb2.FileCreateTransactionBody) -> 'FileCreateTransaction':
        """
        Initializes a new FileCreateTransaction instance from a protobuf object.

        Args:
            proto (FileCreateTransactionBody): The protobuf object to initialize from.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self.keys = [PublicKey._from_proto(key) for key in proto.keys.keys] if proto.keys.keys else []
        self.contents = proto.contents 
        self.expiration_time = Timestamp._from_protobuf(proto.expirationTime) if proto.expirationTime else None
        self.file_memo = proto.memo 
        return self