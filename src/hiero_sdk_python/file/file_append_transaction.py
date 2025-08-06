"""
Represents a file append transaction on the network.

This transaction appends data to an existing file on the network. If a file has multiple keys,
all keys must sign to modify its contents.

The transaction supports chunking for large files, automatically breaking content into
smaller chunks if the content exceeds the chunk size limit.

Inherits from the base Transaction class and implements the required methods
to build and execute a file append transaction.
"""

import math
from typing import Optional
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.hapi.services import file_append_pb2, timestamp_pb2

# pylint: disable=too-many-instance-attributes
class FileAppendTransaction(Transaction):
    """
    Represents a file append transaction on the network.
    
    This transaction appends data to an existing file on the network. If a file has multiple keys,
    all keys must sign to modify its contents.
    
    The transaction supports chunking for large files, automatically breaking content into
    smaller chunks if the content exceeds the chunk size limit.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a file append transaction.
    """
    def __init__(self, file_id: Optional[FileId] = None, contents: Optional[str | bytes] = None,
                 max_chunks: Optional[int] = None, chunk_size: Optional[int] = None):
        """
        Initializes a new FileAppendTransaction instance with the specified parameters.

        Args:
            file_id (Optional[FileId], optional): The ID of the file to append to.
            contents (Optional[str | bytes], optional): The contents to append to the file.                 
            Strings will be automatically encoded as UTF-8 bytes.
            max_chunks (Optional[int], optional): Maximum number of chunks allowed. Defaults to 20.
            chunk_size (Optional[int], optional): Size of each chunk in bytes. Defaults to 4096.
        """
        super().__init__()
        self.file_id: Optional[FileId] = file_id
        self.contents: Optional[bytes] = self._encode_contents(contents)
        self.max_chunks: int = max_chunks if max_chunks is not None else 20
        self.chunk_size: int = chunk_size if chunk_size is not None else 4096
        self._default_transaction_fee = Hbar(5).to_tinybars()

        # Internal tracking for chunking
        self._current_chunk_index: int = 0
        self._total_chunks: int = self._calculate_total_chunks()
        self._transaction_ids: list[TransactionId] = []
        self._signing_keys: list = []  # Store all signing keys for multi-chunk transactions

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

    def set_file_id(self, file_id: FileId) -> 'FileAppendTransaction':
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

    def set_contents(self, contents: Optional[str | bytes]) -> 'FileAppendTransaction':
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

    def set_max_chunks(self, max_chunks: int) -> 'FileAppendTransaction':
        """
        Sets the maximum number of chunks allowed for this transaction.

        Args:
            max_chunks (int): The maximum number of chunks allowed.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.max_chunks = max_chunks
        return self

    def set_chunk_size(self, chunk_size: int) -> 'FileAppendTransaction':
        """
        Sets the chunk size for this transaction.

        Args:
            chunk_size (int): The size of each chunk in bytes.

        Returns:
            FileAppendTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.chunk_size = chunk_size
        self._total_chunks = self._calculate_total_chunks()
        return self

    def build_transaction_body(self):
        """
        Builds the transaction body for this file append transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        # Calculate the current chunk's content
        if self.file_id is None:
            raise ValueError("Missing required FileID")
            
        if self.contents is None:
            chunk_contents = b''
        else:
            start_index = self._current_chunk_index * self.chunk_size
            end_index = min(start_index + self.chunk_size, len(self.contents))
            chunk_contents = self.contents[start_index:end_index]

        file_append_body = file_append_pb2.FileAppendTransactionBody(
            fileID=self.file_id._to_proto() if self.file_id else None,
            contents=chunk_contents
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.fileAppend.CopyFrom(file_append_body)
        return transaction_body

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
        return _Method(
            transaction_func=channel.file.appendContent,
            query_func=None
        )

    def _from_proto(self, proto) -> 'FileAppendTransaction':
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

    def _validate_chunking(self):
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


    def freeze_with(self, client):
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

        if self.transaction_id is None:
            self.transaction_id = client.generate_transaction_id()

        # Generate transaction IDs for all chunks
        self._transaction_ids = []
        base_timestamp = self.transaction_id.valid_start

        for i in range(self.get_required_chunks()):
            if i == 0:
                # First chunk uses the original transaction ID
                chunk_transaction_id = self.transaction_id
            else:
                # Subsequent chunks get incremented timestamps
                # Add i nanoseconds to space out chunks
                chunk_valid_start = timestamp_pb2.Timestamp(
                    seconds=base_timestamp.seconds,
                    nanos=base_timestamp.nanos + i
                )
                chunk_transaction_id = TransactionId(
                    account_id=self.transaction_id.account_id,
                    valid_start=chunk_valid_start
                )
            self._transaction_ids.append(chunk_transaction_id)

        # We iterate through every node in the client's network
        # For each node, set the node_account_id and build the transaction body
        # This allows the transaction to be submitted to any node in the network
        for node in client.network.nodes:
            self.node_account_id = node._account_id
            transaction_body = self.build_transaction_body()
            self._transaction_body_bytes[node._account_id] = transaction_body.SerializeToString()

        # Set the node account id to the current node in the network
        self.node_account_id = client.network.current_node._account_id

        return self


    def execute(self, client):
        """
        Executes the file append transaction.
        
        For multi-chunk transactions, this method will execute all chunks sequentially.
        
        Args:
            client: The client to execute the transaction with.
            
        Returns:
            TransactionReceipt: The receipt from the first chunk execution.
        """
        self._validate_chunking()

        if self.get_required_chunks() == 1:
            # Single chunk transaction
            return super().execute(client)

        # Multi-chunk transaction - execute all chunks
        responses = []

        for chunk_index in range(self.get_required_chunks()):
            self._current_chunk_index = chunk_index

            # Set the transaction ID for this chunk
            if self._transaction_ids and chunk_index < len(self._transaction_ids):
                self.transaction_id = self._transaction_ids[chunk_index]
            # Clear the frozen state to allow rebuilding with new transaction ID
            self._transaction_body_bytes.clear()
            self._signature_map.clear()

            # Freeze the transaction for this chunk if not already frozen
            self.freeze_with(client)

            # Sign with all stored signing keys for this chunk
            for signing_key in self._signing_keys:
                # Call parent sign directly to avoid modifying _signing_keys
                super().sign(signing_key)


            # Execute the chunk
            response = super().execute(client)
            responses.append(response)

            # Return the first response (as per JavaScript implementation)
            return responses[0] if responses else None

    def sign(self, private_key):
        """
        Signs the transaction using the provided private key.
            
        For multi-chunk transactions, this stores the signing key for later use.
        
        Args:
            private_key (PrivateKey): The private key to sign the transaction with.

        Returns:
            FileAppendTransaction: The current transaction instance for method chaining.
        """
        # Store the signing key for multi-chunk transactions (avoid duplicates)
        if private_key not in self._signing_keys:
            self._signing_keys.append(private_key)

        # Call the parent sign method for the current transaction
        return super().sign(private_key)
