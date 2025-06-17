from collections import defaultdict
from functools import cached_property
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.hapi.services import transaction_record_pb2


class TransactionRecord():
    """
    Represents a transaction record on the network.
    """

    def __init__(self, record_proto : 'transaction_record_pb2.TransactionRecord', transaction_id : TransactionId = None):
        """
        Initializes the TransactionRecord with the provided protobuf record.
        """
        self._transaction_id : TransactionId = transaction_id
        self._record_proto = record_proto

    @cached_property
    def receipt(self):
        """
        Returns the receipt associated with the transaction record.
        """
        return TransactionReceipt._from_proto(self._record_proto.receipt)

    @property
    def transaction_id(self):
        """
        Returns the transaction ID of the transaction record.
        """
        return self._transaction_id

    @property
    def transaction_hash(self):
        """
        Returns the transaction hash of the transaction record.
        """
        return self._record_proto.transactionHash

    @property
    def transaction_memo(self):
        """
        Returns the transaction memo of the transaction record.
        """
        return self._record_proto.memo

    @property
    def transaction_fee(self):
        """
        Returns the transaction fee of the transaction record.
        """
        return self._record_proto.transactionFee

    @cached_property
    def token_transfers(self):
        """
        Returns the token transfers associated with the transaction record.

        Returns:
            dict[TokenId, dict[AccountId, int]]: A nested dictionary mapping token IDs to account transfer amounts
        """
        token_transfers = defaultdict(lambda: defaultdict(int))
        
        for token_transfer_list in self._record_proto.tokenTransferLists:
            token_id = TokenId._from_proto(token_transfer_list.token)
            for transfer in token_transfer_list.transfers:
                account_id = AccountId._from_proto(transfer.accountID)
                token_transfers[token_id][account_id] = transfer.amount
        
        return token_transfers

    @cached_property
    def nft_transfers(self):
        """
        Returns a dictionary mapping TokenId to a list of NFT transfers that occurred in this transaction.

        Returns:
            dict[TokenId, list[TokenNftTransfer]]: A dictionary mapping token IDs to their NFT transfers
        """
        nft_transfers = defaultdict(list[TokenNftTransfer])
         
        for token_transfer_list in self._record_proto.tokenTransferLists:
            token_id = TokenId._from_proto(token_transfer_list.token)
            for nft_transfer in token_transfer_list.nftTransfers:
                sender = AccountId._from_proto(nft_transfer.senderAccountID)
                receiver = AccountId._from_proto(nft_transfer.receiverAccountID)
                nft_transfers[token_id].append(TokenNftTransfer(
                    sender,
                    receiver, 
                    nft_transfer.serialNumber,
                    nft_transfer.is_approval
                ))
                 
        return nft_transfers

    @cached_property
    def transfers(self):
        """
        Returns a dictionary mapping AccountId to HBAR amount for all transfers in this transaction.
        This includes:
        - The node fee payment
        - The network/service fee
        - The transaction fee
        - Any other HBAR transfers that were part of the transaction
        
        Returns:
            dict[AccountId, int]: A dictionary mapping account IDs to transfer amounts
        """
        transfers = defaultdict(int)
        
        for transfer in self._record_proto.transferList.accountAmounts:
            account_id = AccountId._from_proto(transfer.accountID)
            transfers[account_id] += transfer.amount
        
        return transfers
    
    @classmethod
    def _from_proto(cls, proto, transaction_id=None):
        """
        Creates a TransactionRecord from a protobuf record.

        Args:
            proto: The protobuf transaction record
            transaction_id: Optional transaction ID to associate with the record
        """
        return cls(proto, transaction_id)

    def _to_proto(self):
        """
        Returns the underlying protobuf transaction record.
        """
        return self._record_proto