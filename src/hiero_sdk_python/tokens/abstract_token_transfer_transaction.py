from collections import defaultdict
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_transfer_list import TokenTransferList
from hiero_sdk_python.transaction.transaction import Transaction

class AbstractTokenTransferTransaction(Transaction):
    def __init__(self):
        """
        Initializes a new AbstractTokenTransferTransaction instance.
        """
        super().__init__()
        self.token_transfers: list[TokenTransfer] = []
        self.nft_transfers: list[TokenNftTransfer] = []
        self._default_transaction_fee = 100_000_000


    def build_token_transfers(self) -> 'list[basic_types_pb2.TokenTransferList]':
        """
        Aggregates all individual fungible token transfers and NFT transfers into
        a list of TokenTransferList objects, where each TokenTransferList groups
        transfers for a specific token ID.

        Returns:
            list[basic_types_pb2.TokenTransferList]: A list of TokenTransferList objects,
            each grouping transfers for a specific token ID.
        """
        transfer_list = defaultdict(TokenTransferList)

        for token_transfer in self.token_transfers:
            if token_transfer.token_id not in transfer_list:
                transfer_list[token_transfer.token_id] = TokenTransferList(
                    token_transfer.token_id, 
                    expected_decimals=token_transfer.expected_decimals
                )            

            transfer_list[token_transfer.token_id].add_token_transfer(token_transfer)

        for nft_transfer in self.nft_transfers:
            if nft_transfer.token_id not in transfer_list:
                transfer_list[nft_transfer.token_id] = TokenTransferList(
                    nft_transfer.token_id 
                )

            transfer_list[nft_transfer.token_id].add_nft_transfer(nft_transfer)

        token_transfers: list[basic_types_pb2.TokenTransferList] = []

        for transfer in list(transfer_list.values()):
            token_transfers.append(transfer._to_proto())
        
        return token_transfers
