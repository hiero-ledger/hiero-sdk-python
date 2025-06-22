import time
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import file_create_pb2
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
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
    def __init__(self, keys: list[PublicKey] = [], contents: bytes = None, expiration_time: Timestamp = None, file_memo: str = None):
        """
        Initializes a new FileCreateTransaction instance with the specified parameters.

        Args:
            keys (list[PublicKey], optional): The keys that are allowed to update/delete the file.
            contents (bytes, optional): The contents of the file to create.
            expiration_time (Timestamp, optional): The time at which the file should expire.
            file_memo (str, optional): A memo to include with the file.
        """
        super().__init__()
        self.keys: list[PublicKey] = keys
        self.contents: bytes = contents
        self.expiration_time: Timestamp = expiration_time if expiration_time else Timestamp(int(time.time()) + 7890000, 0)
        self.file_memo: str = file_memo
        self._default_transaction_fee = Hbar(5).to_tinybars()

    def set_keys(self, keys: list[PublicKey] | PublicKey) -> 'FileCreateTransaction':
        """
        Sets the keys for this file create transaction.

        Args:
            keys (list[PublicKey] | PublicKey): The keys to set for the file. Can be a list of PublicKey objects.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.keys = [keys] if isinstance(keys, PublicKey) else keys
        return self

    def set_contents(self, contents: bytes) -> 'FileCreateTransaction':
        """
        Sets the contents for this file create transaction.

        Args:
            contents (bytes): The contents of the file to create.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contents = contents
        return self

    def set_expiration_time(self, expiration_time: Timestamp) -> 'FileCreateTransaction':
        """
        Sets the expiration time for this file create transaction.

        Args:
            expiration_time (Timestamp): The expiration time for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self
    
    def set_file_memo(self, file_memo: str) -> 'FileCreateTransaction':
        """
        Sets the memo for this file create transaction.

        Args:
            file_memo (str): The memo to set for the file.

        Returns:
            FileCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_memo = file_memo
        return self
        
    def build_transaction_body(self):
        """
        Builds the transaction body for this file create transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        file_create_body = file_create_pb2.FileCreateTransactionBody(
            keys=KeyListProto(keys=[key._to_proto() for key in self.keys or []]),
            contents=self.contents,
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            memo=self.file_memo
        )
        transaction_body = self.build_base_transaction_body()
        transaction_body.fileCreate.CopyFrom(file_create_body)
        return transaction_body
    
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
        self.keys = [PublicKey._from_proto(key) for key in proto.keys.keys]
        self.contents = proto.contents
        self.expiration_time = Timestamp._from_protobuf(proto.expirationTime)
        self.file_memo = proto.memo
        return self