"""
hiero_sdk_python.tokens.token_mint_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenMintTransaction, a subclass of Transaction for minting fungible and
non-fungible tokens on the Hedera network via the Hedera Token Service (HTS) API.
"""
from typing import List, Optional, Union
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_mint_pb2, transaction_body_pb2
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenMintTransaction(Transaction):
    """
    Represents a token minting transaction on the Hedera network.

    Transaction mints tokens (fungible or non-fungible) to the token treasury.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token minting transaction.
    """

    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        amount: Optional[int] = None,
        metadata: Optional[Union[bytes, List[bytes]]] = None
    ) -> None:
        """
        Initializes a new TokenMintTransaction Custom instance with optional keyword arguments.

        Args:
            token_id (TokenId, optional): The ID of the token to mint.
            amount (int, optional): The amount of a fungible token to mint.
            metadata (Union[bytes, List[bytes]], optional): The non-fungible token metadata to mint.
            If a single bytes object is passed, it will be converted internally to [bytes].
        """

        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.amount: Optional[int] = amount
        self.metadata: Optional[Union[bytes,List[bytes]]] = None
        if metadata is not None:
            self.set_metadata(metadata)

        self._default_transaction_fee: int = 3_000_000_000

    def set_token_id(self, token_id: TokenId) -> "TokenMintTransaction":
        """
        Sets the ID of the token to be minted.
        Args:
            token_id (TokenId): The ID of the token to be minted.
        Returns:
            TokenMintTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_amount(self, amount: int) -> "TokenMintTransaction":
        """
        Sets the amount of fungible tokens to mint.
        Args:
            amount (int): The amount of fungible tokens to mint.
        Returns:
            TokenMintTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.amount = amount
        return self

    def set_metadata(self, metadata: Union[bytes, List[bytes]]) -> "TokenMintTransaction":
        """
        Sets the metadata for non-fungible tokens to mint.
        Args:
            metadata (Union[bytes, List[bytes]]): The metadata for non-fungible tokens to mint.
            If a single bytes object is passed, it will be converted internally to [bytes].
        Returns:
            TokenMintTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        if isinstance(metadata, bytes):
            metadata = [metadata]
        self.metadata = metadata
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token minting.
        
        Returns:
            TransactionBody: The protobuf transaction body containing the token minting details.

        Raises:
            ValueError: If required fields are missing or conflicting.
        """
        if not self.token_id:
            raise ValueError("Token ID is required for minting.")

        token_mint_body = (
            self._build_fungible_body()
            if self.amount is not None
            else self._build_nft_body()
            if self.metadata is not None
            else None
        )

        if token_mint_body is None:
            raise ValueError("Either amount or metadata must be provided for token minting.")

        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenMint.CopyFrom(token_mint_body)
        return transaction_body

    def _build_fungible_body(self) -> token_mint_pb2.TokenMintTransactionBody:
        """ Helper method used in build_transaction_body """
        if self.metadata is not None:
            raise ValueError("Specify either amount for fungible tokens or metadata for NFTs, not both.")
        if self.amount is None or self.amount <= 0:
            raise ValueError("Amount to mint must be positive.")

        return token_mint_pb2.TokenMintTransactionBody(
            token=self.token_id._to_proto(),
            amount=self.amount,
            metadata=[],
        )

    def _build_nft_body(self) -> token_mint_pb2.TokenMintTransactionBody:
        """ Helper method used in build_transaction_body """
        if not isinstance(self.metadata, list):
            raise ValueError("Metadata must be a list of byte arrays for NFTs.")
        if not self.metadata:
            raise ValueError("Metadata list cannot be empty for NFTs.")

        return token_mint_pb2.TokenMintTransactionBody(
            token=self.token_id._to_proto(),
            amount=0,
            metadata=self.metadata,
        )

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.mintToken,
            query_func=None
        )
