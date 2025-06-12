from operator import le
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.token_update_nfts_pb2 import TokenUpdateNftsTransactionBody
from google.protobuf.wrappers_pb2 import BytesValue

class TokenUpdateNftsTransaction(Transaction):
    """
    Represents a token update NFTs transaction on the Hedera network.
    
    This transaction updates the metadata of NFTs.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token update NFTs transaction.
    """
    def __init__(self, token_id=None, serial_numbers=None, metadata=None):
        """
        Initializes a new TokenUpdateNftsTransaction instance with optional token_id, serial_numbers, and metadata.

        Args:
            token_id (TokenId, optional): The ID of the token whose NFTs will be updated.
            serial_numbers (list[int], optional): The serial numbers of the NFTs to update.
            metadata (bytes, optional): The new metadata for the NFTs.
        """
        super().__init__()
        self.token_id: TokenId = token_id
        self.serial_numbers: list[int] = serial_numbers if serial_numbers else []
        self.metadata: bytes = metadata

    def set_token_id(self, token_id):
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_serial_numbers(self, serial_numbers):
        self._require_not_frozen()
        self.serial_numbers = serial_numbers
        return self
    
    def set_metadata(self, metadata):
        self._require_not_frozen()
        self.metadata = metadata
        return self
    
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token update NFTs.

        Returns:
            TransactionBody: The protobuf transaction body containing the token update NFTs details.
        
        Raises:
            ValueError: If the token ID and serial numbers are not set or metadata is greater than 100 bytes.
        """
        if not self.token_id:
            raise ValueError("Missing token ID")
        
        if not self.serial_numbers:
            raise ValueError("Missing serial numbers")
        
        if self.metadata and len(self.metadata) > 100:
            raise ValueError("Metadata must be less than 100 bytes")
        
        token_update_body = TokenUpdateNftsTransactionBody(
            token=self.token_id._to_proto(),
            serial_numbers=self.serial_numbers,
            metadata=BytesValue(value=self.metadata)
        )
        
        transaction_body = self.build_base_transaction_body()
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
        
    def _from_proto(self, proto: TokenUpdateNftsTransactionBody):
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