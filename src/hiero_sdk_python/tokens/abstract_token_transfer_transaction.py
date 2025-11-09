"""hiero_sdk_python.tokens.abstract_token_transfer_transaction.py

Abstract base transaction for fungible token and NFT transfers on Hedera.

This module provides the `AbstractTokenTransferTransaction` class, which
encapsulates common logic for grouping and validating multiple token and
NFT transfer operations into Hedera-compatible protobuf messages.
It handles the collection of token and NFT transfers before they are aggregated 
for building the transaction body.
"""
from abc import ABC
from collections import defaultdict
from typing import Any, Dict, Generic, Optional, List, Tuple, TypeVar, Union

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_transfer_list import TokenTransferList
from hiero_sdk_python.transaction.transaction import Transaction

T = TypeVar("T", bound="AbstractTokenTransferTransaction[Any]")

class AbstractTokenTransferTransaction(Transaction, ABC, Generic[T]):
    """
    Base transaction class for executing multiple token and NFT transfers.

    Collects fungible and non-fungible token transfers, ensures balance
    rules, and builds the corresponding Hedera protobuf messages. This class 
    is typically inherited by concrete transaction types like `TransferTransaction`.
    """
    def __init__(self) -> None:
        """
        Initializes a new AbstractTokenTransferTransaction instance.

        Sets up empty lists for token and NFT transfers and defines the default 
        transaction fee.
        """
        super().__init__()
        self.token_transfers: Dict[TokenId, List[TokenTransfer]] = defaultdict(list)
        self.nft_transfers: Dict[TokenId, List[TokenNftTransfer]] = defaultdict(list)
        self._default_transaction_fee: int = 100_000_000

    def _init_token_transfers(
            self,
            token_transfers: Union[Dict[TokenId, Dict[AccountId, int]], List[TokenTransfer]]
        ) -> None:
        """Initializes the transaction with a list of fungible token transfers.

        Iterates through the provided list and adds each transfer using the 
        private `_add_token_transfer` method.

        Args:
            token_transfers (Union[Dict[TokenId, Dict[AccountId, int]], List[TokenTransfer]]):
                A list of initialized TokenTransfer objects.
    
        Raises:
            TypeError: If `token_transfers` is neither a list nor a dictionary.
        """
        if isinstance(token_transfers, list):
            for transfer in token_transfers:
                self._add_token_transfer(
                    transfer.token_id,
                    transfer.account_id,
                    transfer.amount,
                    transfer.expected_decimals,
                    transfer.is_approved
                )
        elif isinstance(token_transfers, dict):
            for token_id, account_transfers in token_transfers.items():
                for account_id, amount in account_transfers.items():
                    self._add_token_transfer(token_id, account_id, amount)
        else:
            raise TypeError(
                "Invalid type for `token_transfers`. Expected a list of TokenTransfer "
                "or a dict[TokenId, dict[AccountId, int]]."
            )

    def _init_nft_transfers(
            self,
            nft_transfers: Union[
                Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]],
                List[TokenNftTransfer]
            ]
        ) -> None:
        """Initializes the transaction with a list of NFT transfers.

        Iterates through the provided list and adds each transfer using the 
        private `_add_nft_transfer` method.

        Args:
            nft_transfers (Union[
                Dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]], List[TokenNftTransfer]]
            ):A list or dictionary describing NFT transfers.

        Raises:
            TypeError: If `nft_transfers` is neither a list nor a dictionary.
        """
        if isinstance(nft_transfers, list):
            for transfer in nft_transfers:
                self._add_nft_transfer(
                    transfer.token_id,
                    transfer.sender_id,
                    transfer.receiver_id,
                    transfer.serial_number,
                    transfer.is_approved
                )
        elif isinstance(nft_transfers, dict):
            for token_id, transfers in nft_transfers.items():
                for sender_id, receiver_id, serial_number, is_approved in transfers:
                    self._add_nft_transfer(
                        token_id, sender_id, receiver_id, serial_number, is_approved
                    )
        else:
            raise TypeError(
                "Invalid type for `nft_transfers`. Expected a list of TokenNftTransfer "
                "or a dict[TokenId, List[Tuple[AccountId, AccountId, int, bool]]]."
            )

    def _add_token_transfer(
            self,
            token_id: TokenId,
            account_id: AccountId,
            amount: int,
            expected_decimals: Optional[int]=None,
            is_approved: bool=False
        ) -> None:
        """Adds a fungible token transfer to the transaction's list.

        Args:
            token_id (TokenId): The ID of the fungible token being transferred.
            account_id (AccountId): The account ID of the sender (negative amount) 
                or receiver (positive amount).
            amount (int): The amount of the token to transfer (in smallest denomination).
                Must be a non-zero integer.
            expected_decimals (Optional[int], optional): The number of decimals 
                expected for the token. Defaults to None.
            is_approved (bool, optional): Whether the transfer is approved. 
                Defaults to False.

        Raises:
            TypeError: If argument types are invalid.
            ValueError: If `amount` is zero.
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

        for transfer in self.token_transfers[token_id]:
            if transfer.account_id == account_id:
                transfer.amount += amount
                transfer.expected_decimals = expected_decimals
                return

        self.token_transfers[token_id].append(
            TokenTransfer(token_id, account_id, amount, expected_decimals, is_approved)
        )

    def _add_nft_transfer(
            self,
            token_id: TokenId,
            sender_id: AccountId,
            receiver_id: AccountId,
            serial_number: int,
            is_approved: bool=False
        ) -> None:
        """Adds an NFT (Non-Fungible Token) transfer to the transaction's list.

        Args:
            token_id (TokenId): The ID of the NFT's token type.
            sender (AccountId): The sender's account ID.
            receiver (AccountId): The receiver's account ID.
            serial_number (int): The unique serial number of the NFT being transferred.
            is_approved (bool, optional): Whether the transfer is approved. 
                Defaults to False.

        Raises:
            TypeError: If any argument type is invalid.
        """
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be a TokenId instance.")
        if not isinstance(sender_id, AccountId):
            raise TypeError("sender_id must be an AccountId instance.")
        if not isinstance(receiver_id, AccountId):
            raise TypeError("receiver_id must be an AccountId instance.")
        if not isinstance(is_approved, bool):
            raise TypeError("is_approved must be a boolean.")

        self.nft_transfers[token_id].append(
            TokenNftTransfer(token_id, sender_id, receiver_id, serial_number, is_approved)
        )

    def add_token_transfer(
            self: T,
            token_id: TokenId,
            account_id: AccountId,
            amount: int
        ) -> T:
        """
        Adds a transfer to token_transfers list 
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self._add_token_transfer(token_id, account_id, amount)
        return self

    def add_token_transfer_with_decimals(
            self: T,
            token_id: TokenId,
            account_id: AccountId,
            amount: int,
            decimals: int
        ) -> T:
        """
        Adds a transfer with expected_decimals to token_transfers list
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.
            decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self._add_token_transfer(token_id, account_id, amount, expected_decimals=decimals)
        return self

    def add_approved_token_transfer(
            self: T,
            token_id: TokenId,
            account_id: AccountId,
            amount: int
        ) -> T:
        """
        Adds a transfer with approve allowance to token_transfers list 
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self._add_token_transfer(token_id, account_id, amount, is_approved=True)
        return self

    def add_approved_token_transfer_with_decimals(
            self: T,
            token_id: TokenId,
            account_id: AccountId,
            amount: int,
            decimals: int
        ) -> T:
        """
        Adds a transfer with expected_decimals and approve allowance to token_transfers list
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.
            decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self._add_token_transfer(token_id, account_id, amount, decimals, True)
        return self

    def add_nft_transfer(
            self: T,
            nft_id: NftId,
            sender_id: AccountId,
            receiver_id: AccountId,
            is_approved: bool = False
        ) -> T:
        """
        Adds a transfer to the nft_transfers

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender_id (AccountId): The sender's account ID.
            receiver_id (AccountId): The receiver's account ID.
            is_approved (bool): Whether the transfer is approved. 

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()

        if not isinstance(nft_id, NftId):
            raise TypeError("nft_id must be a NftId instance.")

        self._add_nft_transfer(
            nft_id.token_id, sender_id, receiver_id, nft_id.serial_number, is_approved
        )
        return self

    def add_approved_nft_transfer(
            self: T,
            nft_id: NftId,
            sender_id: AccountId,
            receiver_id: AccountId
        ) -> T:
        """
        Adds a transfer to the nft_transfers with approved allowance

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender_id (AccountId): The sender's account ID.
            receiver_id (AccountId): The receiver's account ID.

        Returns:
            Self: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()

        if not isinstance(nft_id, NftId):
            raise TypeError("nft_id must be a NftId instance.")

        self._add_nft_transfer(nft_id.token_id, sender_id, receiver_id, nft_id.serial_number, True)
        return self

    def build_token_transfers(self) -> 'List[basic_types_pb2.TokenTransferList]':
        """
        Aggregates all individual fungible token transfers and NFT transfers into
        a list of TokenTransferList objects, where each TokenTransferList groups
        transfers for a specific token ID.

        Performs validation to ensure all fungible token transfers for a given 
        token ID are balanced (net change must be zero).

        Returns:
            list[basic_types_pb2.TokenTransferList]: A list of TokenTransferList objects,
            each grouping transfers for a specific token ID.

        Raises:
            ValueError: If fungible transfers for any token ID are not balanced.
        """
        token_transfer_list: List[TokenTransferList] = []

        # Tokens
        for token_id, token_transfers in self.token_transfers.items():
            token_list = TokenTransferList(
                token=token_id,
                expected_decimals=token_transfers[0].expected_decimals
            )

            for token_transfer in token_transfers:
                token_list.add_token_transfer(token_transfer)

            token_transfer_list.append(token_list)

        # NFTs
        for nft_id, nft_transfers in self.nft_transfers.items():
            nft_list = TokenTransferList(token=nft_id)

            for nft_transfer in nft_transfers:
                nft_list.add_nft_transfer(nft_transfer)

            token_transfer_list.append(nft_list)

        token_transfer_proto: list[basic_types_pb2.TokenTransferList] = []

        # Verify net amount
        for transfer in token_transfer_list:
            net_amount = 0
            for token_transfer in transfer.transfers:
                net_amount += token_transfer.amount

            if net_amount != 0:
                raise ValueError(
                    "All fungible token transfers must be balanced, debits must equal credits."
                )

            token_transfer_proto.append(transfer._to_proto())

        return token_transfer_proto
