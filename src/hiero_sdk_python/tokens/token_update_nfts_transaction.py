"""
hiero_sdk_python.transaction.token_update_nfts_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenUpdateNftsTransaction, a subclass of Transaction for updating
metadata of non-fungible tokens (NFTs) on the Hedera network via HTS.
"""
from operator import le
from typing import List, Optional

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import token_update_nfts_pb2,transaction_body_pb2
from google.protobuf.wrappers_pb2 import BytesValue

class TokenUpdateNftsTransaction(Transaction):
    """
    Represents a token update NFTs transaction on the Hedera network.
    
    This transaction updates the metadata of NFTs.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token update NFTs transaction.
    """
    def __init__(
        self, 
        token_id: Optional[TokenId] = None, 
        serial_numbers: Optional[List[int]] = None, 
        metadata: Optional[bytes] = None
    ) -> None:
        """
        Initializes a new TokenUpdateNftsTransaction instance:
        with optional token_id, serial_numbers, and metadata.

        Args:
            token_id (TokenId, optional): The ID of the token whose NFTs will be updated.
            serial_numbers (list[int], optional): The serial numbers of the NFTs to update.
            metadata (bytes, optional): The new metadata for the NFTs.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.serial_numbers: List[int] = serial_numbers if serial_numbers else []
        self.metadata: Optional[bytes] = metadata

    def set_token_id(self, token_id: TokenId) -> "TokenUpdateNftsTransaction":
        """
        Sets the token ID for this update NFTs transaction.
        Args:
            token_id (TokenId): The ID of the token whose NFTs will be updated.
        Returns:
            TokenUpdateNftsTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_serial_numbers(self, serial_numbers: List[int]) -> "TokenUpdateNftsTransaction":
        """
            Sets the serial numbers of the NFTs to update.
        Args:
            serial_numbers (list[int]): A list of serial numbers for the NFTs to update.
        Returns:
            TokenUpdateNftsTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.serial_numbers = serial_numbers
        return self

    def set_metadata(self, metadata: bytes) -> "TokenUpdateNftsTransaction":
        """
        Sets the metadata for the NFTs to update.
        Args:
            metadata (bytes): The new metadata for the NFTs.
        Returns:
            TokenUpdateNftsTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.metadata = metadata
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token update NFTs.

        Returns:
            TransactionBody: The protobuf transaction body containing the token update NFTs details.
        
        Raises:
            ValueError: If the token ID and serial numbers are not set 
            or metadata is greater than 100 bytes.
        """
        if not self.token_id:
            raise ValueError("Missing token ID")

        if not self.serial_numbers:
            raise ValueError("Missing serial numbers")

        if self.metadata and len(self.metadata) > 100:
            raise ValueError("Metadata must be less than 100 bytes")
        
        token_update_body = token_update_nfts_pb2.TokenUpdateNftsTransactionBody(
            token=self.token_id._to_proto(),
            serial_numbers=self.serial_numbers,
            metadata=BytesValue(value=self.metadata)
        )

        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.token_update_nfts.CopyFrom(token_update_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token update NFTs transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to update NFTs.
        """
        return _Method(
            transaction_func=channel.token.updateNfts,
            query_func=None
        )
        
    def _from_proto(self, proto: token_update_nfts_pb2.TokenUpdateNftsTransactionBody) -> "TokenUpdateNftsTransaction":
        """
        Deserializes a TokenUpdateNftsTransactionBody from a protobuf object.

        Args:
            proto (TokenUpdateNftsTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenUpdateNftsTransaction: Returns self for method chaining.
        """
        self.token_id = TokenId._from_proto(proto.token)
        self.serial_numbers = proto.serial_numbers
        self.metadata = proto.metadata.value
        return self
