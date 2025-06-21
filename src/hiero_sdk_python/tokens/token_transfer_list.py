from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer

class TokenTransferList:
    """
    This class encapsulates the details of a list of token transfers, including fungible
    token transfers, non-fungible token (NFT) transfers, and expected decimal information.
    """
    def __init__(self, token: TokenId, transfers: list[TokenTransfer]=None, nft_transfers: list[TokenNftTransfer]=None, expected_decimals: int=None):
        """
        Initializes a new TokenTransferList instance.

        Args:
            token (TokenId): Thhe ID of the token being transferred.
            transfers (optional, list[TokenTransfer]): A list of fungible token transfers.
            nft_transfers (optional, list[TokenNftTransfer]): A list of NFT transfers.
            expected_decimals (optional, int): The number specifying the amount in the smallest denomination.
        """
        self.token: TokenId = token
        self.transfers: list[TokenTransfer] = []
        self.nft_transfers: list[TokenNftTransfer] = []
        self.expected_decimals: int = expected_decimals

        if (transfers):
            self.transfers = transfers
        if (nft_transfers):
            self.nft_transfers = nft_transfers

    def add_token_transfer(self, transfer: TokenTransfer):
        """
        Adds a fungible token transfer to the list of transfers.

        Args:
            transfer (TokenTransfer): The fungible token transfer to add.
        """
        self.transfers.append(transfer)

    def add_nft_transfer(self, transfer: TokenNftTransfer):
        """
        Adds an NFT transfer to the list of NFT transfers.

        Args:
            transfer (TokenNftTransfer): The NFT transfer to add.
        """
        self.nft_transfers.append(transfer)

    def _to_proto(self):
        """
        Converts this TokenTransferList instance to its protobuf representation.

        Returns:
            TokenTransferList: The protobuf representation of this TokenTransferList.
        """
        proto = basic_types_pb2.TokenTransferList(
            token=self.token._to_proto(),
            expected_decimals={'value':self.expected_decimals} if self.expected_decimals else None
        )

        for transfer in self.transfers:
            proto.transfers.append(transfer._to_proto())

        for transfer in self.nft_transfers:
            proto.nftTransfers.append(transfer._to_proto())

        return proto
    
    def __str__(self):
        """
        Returns a string representation of this TokenTransferList instance.
        
        Returns:
            str: A string representation of this TokenTransferList.
        """
        return f"TokenTransferList(token={self.token},transfers={self.transfers},nft_transfers={self.nft_transfers})"
