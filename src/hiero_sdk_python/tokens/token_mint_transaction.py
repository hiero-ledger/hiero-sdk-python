from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_mint_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenMintTransaction(Transaction):
    """
    Represents a token minting transaction on the Hedera network.

    This transaction mints new tokens (fungible or non-fungible) and delivers them to the token treasury.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token minting transaction.
    """

    def __init__(self, token_id=None, amount=None, metadata=None):
        """
        Initializes a new TokenMintTransaction Custom instance with optional keyword arguments.

        Args:
            token_id (TokenId, optional): The ID of the token to mint.
            amount (int, optional): The amount of a fungible token to mint.
            metadata (Union[bytes, List[bytes]], optional): The non-fungible token metadata to mint.
            If a single bytes object is passed, it will be converted internally to [bytes].
        """
   
        super().__init__()
        self.token_id = token_id
        self.amount = amount
        self.metadata = None  
        if metadata is not None:
            self.set_metadata(metadata)

        self._default_transaction_fee = 3_000_000_000

    def set_token_id(self, token_id):
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_amount(self, amount):
        self._require_not_frozen()
        self.amount = amount
        return self

    def set_metadata(self, metadata):
        self._require_not_frozen()
        if isinstance(metadata, bytes):
            metadata = [metadata]
        self.metadata = metadata
        return self
        
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token minting.
        
        Returns:
            TransactionBody: The protobuf transaction body containing the token minting details.

        Raises:
            ValueError: If required fields are missing or conflicting.
        """
        if not self.token_id:
            raise ValueError("Token ID is required for minting.")

        if (self.amount is not None) and (self.metadata is not None):
            raise ValueError("Specify either amount for fungible tokens or metadata for NFTs, not both.")

        if self.amount is not None:
            # Minting fungible tokens
            if self.amount <= 0:
                raise ValueError("Amount to mint must be positive.")
        
            token_mint_body = token_mint_pb2.TokenMintTransactionBody(
                token=self.token_id._to_proto(),
                amount=self.amount,
                metadata=[] # Must be empty for fungible tokens
            )

        elif self.metadata is not None:

            # Minting NFTs
            if not isinstance(self.metadata, list):
                raise ValueError("Metadata must be a list of byte arrays for NFTs.")
            if not self.metadata:
                raise ValueError("Metadata list cannot be empty for NFTs.")
            
            token_mint_body = token_mint_pb2.TokenMintTransactionBody(
                token=self.token_id._to_proto(),
                amount=0,  # Must be zero for NFTs
                metadata=self.metadata
            )

        else:
            raise ValueError("Either amount or metadata must be provided for token minting.")

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenMint.CopyFrom(token_mint_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.mintToken,
            query_func=None
        )