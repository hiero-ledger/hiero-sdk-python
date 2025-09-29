"""
Defines TransferTransaction for transferring HBAR or tokens between accounts.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from google.protobuf.wrappers_pb2 import UInt32Value

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import basic_types_pb2, crypto_transfer_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.hbar_transfer import HbarTransfer
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.transaction.transaction import Transaction


class TransferTransaction(Transaction):
    """
    Represents a transaction to transfer HBAR or tokens between accounts.
    """

    def __init__(
        self,
        hbar_transfers: Optional[Dict[AccountId, int]] = None,
        token_transfers: Optional[Dict[TokenId, Dict[AccountId, int]]] = None,
        nft_transfers: Optional[Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]]] = None,
    ) -> None:
        """
        Initializes a new TransferTransaction instance.

        Args:
            hbar_transfers (dict[AccountId, int], optional): Initial HBAR transfers.
            token_transfers (dict[TokenId, dict[AccountId, int]], optional):
                Initial token transfers.
            nft_transfers (dict[TokenId, list[tuple[AccountId, AccountId, int, bool]]], optional):
                Initial NFT transfers.
        """
        super().__init__()
        self.hbar_transfers: List[HbarTransfer] = []
        self.token_transfers: Dict[TokenId, List[TokenTransfer]] = defaultdict(list)
        self.nft_transfers: Dict[TokenId, List[TokenNftTransfer]] = defaultdict(list)
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

    def _init_nft_transfers(
        self, nft_transfers: Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]]
    ) -> None:
        """
        Initializes NFT transfers from a dictionary.
        The dictionary should map TokenId to a list of tuples containing sender_id, receiver_id,
        serial_number, and is_approved.
        """
        for token_id, transfers in nft_transfers.items():
            for sender_id, receiver_id, serial_number, is_approved in transfers:
                self.add_nft_transfer(
                    NftId(token_id, serial_number), sender_id, receiver_id, is_approved
                )

    def _validate_token_transfer(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        expected_decimals: Optional[int],
        is_approved: bool,
    ) -> None:
        """
        Validates a token transfer.
        """
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be a TokenId instance.")
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")
        if expected_decimals is not None and not isinstance(expected_decimals, int):
            raise TypeError("expected_decimals must be an integer.")
        if not isinstance(is_approved, bool):
            raise TypeError("is_approved must be a boolean.")

    def _add_hbar_transfer(
        self, account_id: AccountId, amount: int, is_approved: bool = False
    ) -> "TransferTransaction":
        """
        Internal method to add a HBAR transfer to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the HBAR to transfer.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")
        if not isinstance(is_approved, bool):
            raise TypeError("is_approved must be a boolean.")

        for transfer in self.hbar_transfers:
            if transfer.account_id == account_id:
                transfer.amount += amount
                return self

        self.hbar_transfers.append(HbarTransfer(account_id, amount, is_approved))
        return self

    def _add_token_transfer(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        is_approved: bool = False,
        expected_decimals: Optional[int] = None,
    ) -> "TransferTransaction":
        """
        Internal method to add a token transfer to the transaction.
        When accumulating transfers for the same token and account, sets is_approved
        for all transfers of that token and updates expected_decimals.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to transfer.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
            expected_decimals (int, optional): The number specifying
                the amount in the smallest denomination.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self._validate_token_transfer(token_id, account_id, amount, expected_decimals, is_approved)
        for transfer in self.token_transfers[token_id]:
            if transfer.account_id == account_id:
                transfer.amount += amount
                transfer.expected_decimals = expected_decimals
                return self

        self.token_transfers[token_id].append(
            TokenTransfer(token_id, account_id, amount, expected_decimals, is_approved)
        )
        return self

    def _add_nft_transfer(
        self, nft_id: NftId, sender_id: AccountId, receiver_id: AccountId, is_approved: bool = False
    ) -> "TransferTransaction":
        """
        Internal method to add a NFT transfer to the transaction.

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender_id (AccountId): The sender's account ID.
            receiver_id (AccountId): The receiver's account ID.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        if not isinstance(nft_id, NftId):
            raise TypeError("nft_id must be a NftId instance.")
        if not isinstance(sender_id, AccountId):
            raise TypeError("sender_id must be an AccountId instance.")
        if not isinstance(receiver_id, AccountId):
            raise TypeError("receiver_id must be an AccountId instance.")
        if not isinstance(is_approved, bool):
            raise TypeError("is_approved must be a boolean.")

        self.nft_transfers[nft_id.token_id].append(
            TokenNftTransfer(
                nft_id.token_id, sender_id, receiver_id, nft_id.serial_number, is_approved
            )
        )
        return self

    def add_hbar_transfer(self, account_id: AccountId, amount: int) -> "TransferTransaction":
        """
        Adds a HBAR transfer to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the HBAR to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_hbar_transfer(account_id, amount, False)
        return self

    def add_token_transfer(
        self, token_id: TokenId, account_id: AccountId, amount: int
    ) -> "TransferTransaction":
        """
        Adds a token transfer to the transaction.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_token_transfer(token_id, account_id, amount, False, None)
        return self

    def add_nft_transfer(
        self, nft_id: NftId, sender_id: AccountId, receiver_id: AccountId, is_approved: bool = False
    ) -> "TransferTransaction":
        """
        Adds a NFT transfer to the transaction.

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender_id (AccountId): The sender's account ID.
            receiver_id (AccountId): The receiver's account ID.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_nft_transfer(nft_id, sender_id, receiver_id, is_approved)
        return self

    def add_approved_hbar_transfer(
        self, account_id: AccountId, amount: int
    ) -> "TransferTransaction":
        """
        Adds a HBAR transfer with approval to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the HBAR to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_hbar_transfer(account_id, amount, True)
        return self

    def add_approved_token_transfer(
        self, token_id: TokenId, account_id: AccountId, amount: int
    ) -> "TransferTransaction":
        """
        Adds a token transfer with approval to the transaction.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_token_transfer(token_id, account_id, amount, True, None)
        return self

    def add_approved_nft_transfer(
        self, nft_id: NftId, sender_id: AccountId, receiver_id: AccountId
    ) -> "TransferTransaction":
        """
        Adds a NFT transfer with approval to the transaction.

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender_id (AccountId): The sender's account ID.
            receiver_id (AccountId): The receiver's account ID.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_nft_transfer(nft_id, sender_id, receiver_id, True)
        return self

    def add_approved_token_transfer_with_decimals(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        expected_decimals: int,
    ) -> "TransferTransaction":
        """
        Adds an approved token transfer with decimals to the transaction.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to transfer.
            expected_decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_token_transfer(token_id, account_id, amount, True, expected_decimals)
        return self

    def add_token_transfer_with_decimals(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        expected_decimals: int,
    ) -> "TransferTransaction":
        """
        Adds a token transfer with decimals to the transaction.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to transfer.
            expected_decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_token_transfer(token_id, account_id, amount, False, expected_decimals)
        return self

    def _build_proto_body(self) -> crypto_transfer_pb2.CryptoTransferTransactionBody:
        """
        Returns the protobuf body for the transfer transaction.
        """
        crypto_transfer_tx_body = crypto_transfer_pb2.CryptoTransferTransactionBody()

        # HBAR
        if self.hbar_transfers:
            transfer_list = basic_types_pb2.TransferList()
            for hbar_transfer in self.hbar_transfers:
                transfer_list.accountAmounts.append(hbar_transfer._to_proto())

            crypto_transfer_tx_body.transfers.CopyFrom(transfer_list)

        # NFTs
        for token_id, nft_transfers in self.nft_transfers.items():
            token_transfer_list = basic_types_pb2.TokenTransferList(token=token_id._to_proto())
            for transfer in nft_transfers:
                token_transfer_list.nftTransfers.append(transfer._to_proto())

            crypto_transfer_tx_body.tokenTransfers.append(token_transfer_list)

        # Tokens
        for token_id, token_transfers in self.token_transfers.items():
            token_transfer_list = basic_types_pb2.TokenTransferList(
                token=token_id._to_proto(),
                expected_decimals=(
                    UInt32Value(value=token_transfers[0].expected_decimals)
                    if token_transfers[0].expected_decimals is not None
                    else None
                ),
            )
            for token_transfer in token_transfers:
                token_transfer_list.transfers.append(token_transfer._to_proto())

            crypto_transfer_tx_body.tokenTransfers.append(token_transfer_list)

        return crypto_transfer_tx_body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for a transfer transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        crypto_transfer_tx_body = self._build_proto_body()

        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoTransfer.CopyFrom(crypto_transfer_tx_body)

        return transaction_body

    def build_scheduled_body(self) -> "SchedulableTransactionBody":
        """
        Builds the transaction body for this transfer transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        crypto_transfer_tx_body = self._build_proto_body()

        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.cryptoTransfer.CopyFrom(crypto_transfer_tx_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(transaction_func=channel.crypto.cryptoTransfer, query_func=None)
