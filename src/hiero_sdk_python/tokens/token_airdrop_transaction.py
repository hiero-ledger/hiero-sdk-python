"""
hiero_sdk_python.tokens.token_airdrop_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenAirdropTransaction, a concrete transaction class for distributing
both fungible tokens and NFTs to multiple accounts on the Hedera network via
Hedera Token Service (HTS) airdrop functionality.
"""
from typing import Optional, List

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.abstract_token_transfer_transaction import AbstractTokenTransferTransaction
from hiero_sdk_python.hapi.services import token_airdrop_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

class TokenAirdropTransaction(AbstractTokenTransferTransaction["TokenAirdropTransaction"]):
    """
    Represents a token airdrop transaction on the Hedera network.

    The TokenAirdropTransaction allows users to transfer tokens to multiple accounts,
    handling both fungible tokens and NFTs.
    """
    def __init__(
            self,
            token_transfers: Optional[List[TokenTransfer]] = None,
            nft_transfers: Optional[List[TokenNftTransfer]] = None
        ) -> None:
        """
        Initializes a new TokenAirdropTransaction instance.

        Args:
            token_transfers (list[TokenTransfer], optional): 
                Initial list of fungible token transfers.
            nft_transfers (list[TokenNftTransfer], optional): Initial list of NFT transfers.
        """
        super().__init__()
        if token_transfers:
            self._init_token_transfers(token_transfers)
        if nft_transfers:
            self._init_nft_transfers(nft_transfers)
    
    def _build_proto_body(self) -> token_airdrop_pb2.TokenAirdropTransactionBody:
        """
        Returns the protobuf body for the token airdrop transaction.
        
        Returns:
            TokenAirdropTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If transfer list is invalid.
        """
        token_transfers = self.build_token_transfers()

        if (len(token_transfers) < 1 or len(token_transfers) > 10):
            raise ValueError(
                "Airdrop transfer list must contain minimum 1 and maximum 10 transfers."
            )

        return token_airdrop_pb2.TokenAirdropTransactionBody(
            token_transfers=token_transfers
        )

    @classmethod
    def _from_proto(cls, proto: token_airdrop_pb2.TokenAirdropTransactionBody) -> "TokenAirdropTransaction":
        """
        Construct an instance of TokenAirdropTransaction from protobuf TokenAirdropTransactionBody.

        Args:
            proto (TokenAirdropTransactionBody): The protobuf TokenAirdropTransctionBody
        """
        token_transfers: List[TokenTransfer] = []
        nft_transfers: List[TokenNftTransfer] = []

        for transfer in proto.token_transfers:
            if transfer.transfers:
                for token_transfer in TokenTransfer._from_proto(transfer):
                    token_transfers.append(token_transfer)

            elif transfer.nftTransfers:
                for nft_transfer in TokenNftTransfer._from_proto(transfer):
                    nft_transfers.append(nft_transfer)

        return cls(
            token_transfers=token_transfers,
            nft_transfers=nft_transfers
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody :
        """
        Builds and returns the protobuf transaction body for token airdrop.
        
        Returns:
            TransactionBody: The protobuf transaction body containing the token airdrop details.
        """
        token_airdrop_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenAirdrop.CopyFrom(token_airdrop_body)
        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token airdrop transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_airdrop_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenAirdrop.CopyFrom(token_airdrop_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        token_service = channel.token
        if token_service is None:
            raise ValueError("Token service not available on channel")

        return _Method(
            transaction_func=token_service.airdropTokens,
            query_func=None
        )
