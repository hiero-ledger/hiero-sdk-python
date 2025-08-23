"""
hiero_sdk_python.tokens.abstract_token_transfer_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Abstract base transaction for fungible token and NFT transfers on Hedera.

This module provides the `AbstractTokenTransferTransaction` class, which
encapsulates common logic for grouping and validating multiple token and
NFT transfer operations into Hedera-compatible protobuf messages.
"""
from typing import Optional, List

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_transfer_list import TokenTransferList
from hiero_sdk_python.transaction.transaction import Transaction

class AbstractTokenTransferTransaction(Transaction):
    """
    Base transaction class for executing multiple token and NFT transfers.

    Collects fungible and non-fungible token transfers, ensures balance
    rules, and builds the corresponding Hedera protobuf messages.
    """
    def __init__(self) -> None:
        """
        Initializes a new AbstractTokenTransferTransaction instance.
        """
        super().__init__()
        self.token_transfers: List[TokenTransfer] = []
        self.nft_transfers: List[TokenNftTransfer] = []
        self._default_transaction_fee: int = 100_000_000

    def _init_token_transfers(
            self,
            token_transfers: List[TokenTransfer]
        ) -> None:
        for transfer in token_transfers:
            self._add_token_transfer(
                transfer.token_id,
                transfer.account_id,
                transfer.amount,
                transfer.expected_decimals,
                transfer.is_approved)

    def _init_nft_transfers(
            self,
            nft_transfers: List[TokenNftTransfer]
        ) -> None:
        for transfer in nft_transfers:
            self._add_nft_transfer(
                transfer.token_id,
                transfer.sender_id,
                transfer.receiver_id,
                transfer.serial_number,
                transfer.is_approved)

    def _add_token_transfer(
            self,
            token_id: TokenId,
            account_id: AccountId,
            amount: int,
            expected_decimals: Optional[int]=None,
            is_approved: bool=False
        ) -> None:
        """
        Adds a token transfer to the transaction.
        """
        if amount == 0:
            raise ValueError("Amount must be a non-zero integer.")

        self.token_transfers.append(
            TokenTransfer(token_id, account_id, amount, expected_decimals, is_approved)
        )

    def _add_nft_transfer(
            self,
            token_id: TokenId,
            sender: AccountId,
            receiver: AccountId,
            serial_number: int,
            is_approved: bool=False
        ) -> None:
        """
        Adds a nft transfer to the transaction.
        """
        self.nft_transfers.append(
            TokenNftTransfer(token_id,sender, receiver, serial_number, is_approved)
        )

    def build_token_transfers(self) -> 'List[basic_types_pb2.TokenTransferList]':
        """
        Aggregates all individual fungible token transfers and NFT transfers into
        a list of TokenTransferList objects, where each TokenTransferList groups
        transfers for a specific token ID.

        Returns:
            list[basic_types_pb2.TokenTransferList]: A list of TokenTransferList objects,
            each grouping transfers for a specific token ID.
        """
        transfer_list: dict[TokenId,TokenTransferList] = {}

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
            net_amount = 0
            for token_transfer in transfer.transfers:
                net_amount += token_transfer.amount

            if net_amount != 0:
                raise ValueError(
                    "All fungible token transfers must be balanced, debits must equal credits.")

            token_transfers.append(transfer._to_proto())

        return token_transfers
