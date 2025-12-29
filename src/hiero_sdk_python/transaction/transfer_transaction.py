"""
Defines TransferTransaction for transferring HBAR or tokens between accounts.
"""

from typing import Dict, List, Optional, Tuple, Union

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hapi.services import basic_types_pb2, crypto_transfer_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.abstract_token_transfer_transaction import (
    AbstractTokenTransferTransaction
)
from hiero_sdk_python.tokens.hbar_transfer import HbarTransfer
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer


class TransferTransaction(AbstractTokenTransferTransaction["TransferTransaction"]):
    """
    Represents a transaction to transfer HBAR or tokens between accounts.
    """

    def __init__(
        self,
        hbar_transfers: Optional[Dict[AccountId, int]] = None,
        token_transfers: Optional[Dict[TokenId, Dict[AccountId, int]]] = None,
        nft_transfers: Optional[Dict[TokenId,
                                     List[Tuple[AccountId, AccountId, int, bool]]]] = None,
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

    def _add_hbar_transfer(
        self, account_id: AccountId, amount: Union[int, Hbar], is_approved: bool = False
    ) -> "TransferTransaction":
        """
        Internal method to add a HBAR transfer to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (Union[int, Hbar]): The amount of the HBAR to transfer.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if isinstance(amount, Hbar):
            amount = amount.to_tinybars()
        elif not isinstance(amount, int):
            raise TypeError("amount must be an int or Hbar instance.")
        if amount == 0:
            raise ValueError("Amount must be a non-zero value.")
        if not isinstance(is_approved, bool):
            raise TypeError("is_approved must be a boolean.")

        for transfer in self.hbar_transfers:
            if transfer.account_id == account_id:
                transfer.amount += amount
                return self

        self.hbar_transfers.append(
            HbarTransfer(account_id, amount, is_approved))
        return self

    def add_hbar_transfer(self, account_id: AccountId, amount: Union[int, Hbar]) -> "TransferTransaction":
        """
        Adds a HBAR transfer to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (Union[int, Hbar]): The amount of the HBAR to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_hbar_transfer(account_id, amount, False)
        return self

    def add_approved_hbar_transfer(
        self, account_id: AccountId, amount: Union[int, Hbar]
    ) -> "TransferTransaction":
        """
        Adds a HBAR transfer with approval to the transaction.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (Union[int, Hbar]): The amount of the HBAR to transfer.

        Returns:
            TransferTransaction: The current instance of the transaction for chaining.
        """
        self._add_hbar_transfer(account_id, amount, True)
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

        # NFTs/Tokens
        token_transfers = self.build_token_transfers()

        for transfer in token_transfers:
            crypto_transfer_tx_body.tokenTransfers.append(transfer)

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

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        """
        Creates a TransferTransaction instance from protobuf components.

        Args:
            transaction_body: The parsed TransactionBody protobuf
            body_bytes (bytes): The raw bytes of the transaction body
            sig_map: The SignatureMap protobuf containing signatures

        Returns:
            TransferTransaction: A new transaction instance with all fields restored
        """
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)

        if transaction_body.HasField("cryptoTransfer"):
            crypto_transfer = transaction_body.cryptoTransfer

            if crypto_transfer.HasField("transfers"):
                for account_amount in crypto_transfer.transfers.accountAmounts:
                    account_id = AccountId._from_proto(
                        account_amount.accountID)
                    amount = account_amount.amount
                    is_approved = account_amount.is_approval
                    transaction.hbar_transfers.append(
                        HbarTransfer(account_id, amount, is_approved)
                    )

            for token_transfer_list in crypto_transfer.tokenTransfers:
                token_id = TokenId._from_proto(token_transfer_list.token)

                for transfer in token_transfer_list.transfers:
                    account_id = AccountId._from_proto(transfer.accountID)
                    amount = transfer.amount
                    is_approved = transfer.is_approval

                    expected_decimals = None
                    if token_transfer_list.HasField("expected_decimals"):
                        expected_decimals = token_transfer_list.expected_decimals.value

                    transaction.token_transfers[token_id].append(
                        TokenTransfer(token_id, account_id, amount,
                                      expected_decimals, is_approved)
                    )

                for nft_transfer in token_transfer_list.nftTransfers:
                    sender_id = AccountId._from_proto(
                        nft_transfer.senderAccountID)
                    receiver_id = AccountId._from_proto(
                        nft_transfer.receiverAccountID)
                    serial_number = nft_transfer.serialNumber
                    is_approved = nft_transfer.is_approval

                    transaction.nft_transfers[token_id].append(
                        TokenNftTransfer(
                            token_id, sender_id, receiver_id, serial_number, is_approved)
                    )

        return transaction
