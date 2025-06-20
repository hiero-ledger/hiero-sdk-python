from typing import Optional, List
from hiero_sdk_python.hapi.services.token_reject_pb2 import TokenReference, TokenRejectTransactionBody
from hiero_sdk_python.hapi.services import transaction_body_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenRejectTransaction(Transaction):
    """
    Represents a token reject transaction on the Hedera network.
    
    This transaction rejects a token transfer.
    Allows users to reject and return unwanted airdrops
    to the treasury account without incurring custom fees.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token reject transaction.
    """
    def __init__(
        self,
        owner_id: Optional[AccountId] = None,
        token_ids: Optional[List[TokenId]] = None,
        nft_ids: Optional[List[NftId]] = None
    ) -> None:
        """
        Initializes a new TokenRejectTransaction instance with optional owner_id, token_ids, and nft_ids.

        Args:
            owner_id (AccountId, optional): The ID of the account to reject the token transfer.
            token_ids (list[TokenId], optional): The IDs of the fungible tokens to reject.
            nft_ids (list[NftId], optional): The IDs of the non-fungible tokens (NFTs) to reject.
        """
        super().__init__()
        self.owner_id: Optional[AccountId] = owner_id
        self.token_ids: List[TokenId] = token_ids if token_ids else []
        self.nft_ids: List[NftId] = nft_ids if nft_ids else []
        
    def set_owner_id(self, owner_id: AccountId) -> "TokenRejectTransaction":
        self._require_not_frozen()
        self.owner_id = owner_id
        return self

    def set_token_ids(self, token_ids: List[TokenId]) -> "TokenRejectTransaction":
        self._require_not_frozen()
        self.token_ids = token_ids
        return self
    
    def set_nft_ids(self, nft_ids: List[NftId]) -> "TokenRejectTransaction":
        self._require_not_frozen()
        self.nft_ids = nft_ids
        return self
    
    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token reject.

        Returns:
            TransactionBody: The protobuf transaction body containing the token reject details.
        """
        token_references = []
        for token_id in self.token_ids:
            token_references.append(TokenReference(fungible_token=token_id._to_proto()))
        for nft_id in self.nft_ids:
            token_references.append(TokenReference(nft=nft_id._to_proto()))
        
        token_reject_body = TokenRejectTransactionBody(
            owner=self.owner_id and self.owner_id._to_proto(),
            rejections=token_references
        )
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenReject.CopyFrom(token_reject_body)
        return transaction_body
    
    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token reject transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to reject tokens.
        """
        return _Method(
            transaction_func=channel.token.rejectToken,
            query_func=None
        )
    
    def _from_proto(self, proto: TokenRejectTransactionBody) -> "TokenRejectTransaction":
        """
        Deserializes a TokenRejectTransactionBody from a protobuf object.

        Args:
            proto (TokenRejectTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenRejectTransaction: Returns self for method chaining.
        """
        self.owner_id = AccountId._from_proto(proto.owner)
        
        # Extract fungible token IDs from rejections with fungible_token field set (using HasField to filter out default/empty values)
        self.token_ids = [TokenId._from_proto(token_id.fungible_token) for token_id in proto.rejections if token_id.HasField('fungible_token')]
        
        # Extract NFT IDs from rejections with nft field set (using HasField to filter out default/empty values)
        self.nft_ids = [NftId._from_proto(nft_id.nft) for nft_id in proto.rejections if nft_id.HasField('nft')]
        
        return self