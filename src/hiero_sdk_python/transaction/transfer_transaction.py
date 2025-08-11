from collections import defaultdict
from typing import Optional, Dict, List, Tuple
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import crypto_transfer_pb2, basic_types_pb2, transaction_body_pb2
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.nft_id import NftId

class TransferTransaction(Transaction):
    """
    Represents a transaction to transfer HBAR or tokens between accounts.
    """

    def __init__(
        self, 
        hbar_transfers:  Optional[Dict[AccountId, int]] = None, 
        token_transfers: Optional[Dict[TokenId, Dict[AccountId, int]]] = None, 
        nft_transfers:   Optional[Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]]] = None
    ) -> None:
        """
        Initializes a new TransferTransaction instance.

        Args:
            hbar_transfers (dict[AccountId, int], optional): Initial HBAR transfers.
            token_transfers (dict[TokenId, dict[AccountId, int]], optional): Initial token transfers.
            nft_transfers (dict[TokenId, list[tuple[AccountId, AccountId, int, bool]]], optional): Initial NFT transfers.
        """
        super().__init__()
        self.hbar_transfers:  Dict[AccountId, int] = defaultdict(int)
        self.token_transfers: Dict[TokenId, Dict[AccountId, int]] = defaultdict(lambda: defaultdict(int))
        self.nft_transfers:   Dict[TokenId, List[TokenNftTransfer]] = defaultdict(list)
        self._default_transaction_fee: int = 100_000_000

        if hbar_transfers:
            self._init_hbar_transfers(hbar_transfers)
        if token_transfers:
            self._init_token_transfers(token_transfers)
        if nft_transfers:
            self._init_nft_transfers(nft_transfers)

    def _init_hbar_transfers(self, hbar_transfers: Dict[AccountId, int]) -> None:
        """
        Initializes HBAR transfers from a dictionary.
        """
        for account_id, amount in hbar_transfers.items():
            self.add_hbar_transfer(account_id, amount)

    def _init_token_transfers(self, token_transfers: Dict[TokenId, Dict[AccountId, int]]) -> None:
        """
        Initializes token transfers from a nested dictionary.
        """
        for token_id, account_transfers in token_transfers.items():
            for account_id, amount in account_transfers.items():
                self.add_token_transfer(token_id, account_id, amount)

    def _init_nft_transfers(self, nft_transfers: Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]]) -> None:
        """
        Initializes NFT transfers from a dictionary.
        The dictionary should map TokenId to a list of tuples containing sender_id, receiver_id,
        serial_number, and is_approved.
        """
        for token_id, transfers in nft_transfers.items():
            for sender_id, receiver_id, serial_number, is_approved in transfers:
                self.add_nft_transfer(NftId(token_id, serial_number), sender_id, receiver_id, is_approved)

    def add_hbar_transfer(self, account_id: AccountId, amount: int) -> "TransferTransaction":
        """
        Adds a HBAR transfer to the transaction.
        """
        self._require_not_frozen()
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")

        self.hbar_transfers[account_id] += amount
        return self

    def add_token_transfer(self, token_id: TokenId, account_id: AccountId, amount: int) -> "TransferTransaction":
        """
        Adds a token transfer to the transaction.
        """
        self._require_not_frozen()
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be a TokenId instance.")
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")

        self.token_transfers[token_id][account_id] += amount
        return self

    def add_nft_transfer(
        self, 
        nft_id: NftId, 
        sender_id: AccountId, 
        receiver_id: AccountId, 
        is_approved: bool = False
    ) -> "TransferTransaction":
        """
        Adds a NFT transfer to the transaction.
        """
        self._require_not_frozen()
        if not isinstance(nft_id, NftId):
            raise TypeError("nft_id must be a NftId instance.")
        if not isinstance(sender_id, AccountId):
            raise TypeError("sender_id must be an AccountId instance.")
        if not isinstance(receiver_id, AccountId):
            raise TypeError("receiver_id must be an AccountId instance.")

        self.nft_transfers[nft_id.token_id].append(TokenNftTransfer(nft_id.token_id, sender_id, receiver_id, nft_id.serial_number, is_approved))
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for a transfer transaction.
        """
        crypto_transfer_tx_body = crypto_transfer_pb2.CryptoTransferTransactionBody()

        # HBAR
        if self.hbar_transfers:
            transfer_list = basic_types_pb2.TransferList()
            for account_id, amount in self.hbar_transfers.items():
                transfer_list.accountAmounts.append(
                    basic_types_pb2.AccountAmount(
                        accountID=account_id._to_proto(),
                        amount=amount,
                    )
                )
            crypto_transfer_tx_body.transfers.CopyFrom(transfer_list)

        # NFTs
        for token_id, nft_transfers in self.nft_transfers.items():
            token_transfer_list = basic_types_pb2.TokenTransferList(
                token=token_id._to_proto()
            )
            for transfer in nft_transfers:
                token_transfer_list.nftTransfers.append(transfer._to_proto())

            crypto_transfer_tx_body.tokenTransfers.append(token_transfer_list)

        # Tokens
        for token_id, token_transfers in self.token_transfers.items():
            token_transfer_list = basic_types_pb2.TokenTransferList(
                token=token_id._to_proto()
            )
            for account_id, amount in token_transfers.items():
                token_transfer_list.transfers.append(
                    basic_types_pb2.AccountAmount(
                        accountID=account_id._to_proto(),
                        amount=amount,
                    )
                )
            crypto_transfer_tx_body.tokenTransfers.append(token_transfer_list)

        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.cryptoTransfer.CopyFrom(crypto_transfer_tx_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.crypto.cryptoTransfer,
            query_func=None
        )