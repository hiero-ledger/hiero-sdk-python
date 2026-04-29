"""
transaction_receipt.py.
~~~~~~~~~~~~~~~~~~~~~~

Defines the TransactionReceipt class, which represents the outcome of a Hedera transaction.

This module provides structured access to fields in a transaction receipt,
including associated IDs like TokenId, TopicId, AccountId, and FileId.
It wraps the underlying protobuf object and exposes key properties.

Classes:
    - TransactionReceipt: Parses and exposes fields from a transaction receipt protobuf.
"""

from __future__ import annotations

from typing import cast

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import response_code_pb2, transaction_receipt_pb2
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId


class TransactionReceipt:
    """
    Represents the receipt of a transaction.

    The receipt contains information about the status and result of a transaction,
    such as the TokenId or AccountId involved.

    Attributes:
        status (ResponseCode): The status code of the transaction.
        _receipt_proto (TransactionReceiptProto): The underlying protobuf receipt.
        _transaction_id (TransactionId): The transaction ID associated with this receipt.
    """

    def __init__(
        self,
        receipt_proto: transaction_receipt_pb2.TransactionReceipt,
        transaction_id: TransactionId | None = None,
        children: list[TransactionReceipt] | None = None,
        duplicates: list[TransactionReceipt] | None = None,
    ) -> None:
        """
        Initializes the TransactionReceipt with the provided protobuf receipt.

        Args:
            receipt_proto (transaction_receipt_pb2.TransactionReceiptProto, optional): The protobuf transaction receipt.
            transaction_id (TransactionId, optional): The transaction ID associated with this receipt.
        """
        self._transaction_id: TransactionId | None = transaction_id
        self.status: response_code_pb2.ResponseCodeEnum | None = receipt_proto.status
        self._receipt_proto: transaction_receipt_pb2.TransactionReceipt = receipt_proto
        self._children: list[TransactionReceipt] = children or []
        self._duplicates: list[TransactionReceipt] = duplicates or []

    @property
    def token_id(self) -> TokenId | None:
        """
        Retrieves the TokenId associated with the transaction receipt, if available.

        Returns:
            TokenId or None: The TokenId if present; otherwise, None.
        """
        if self._receipt_proto.HasField("tokenID") and self._receipt_proto.tokenID.tokenNum != 0:
            return TokenId._from_proto(self._receipt_proto.tokenID)
        return None

    @property
    def topic_id(self) -> TopicId | None:
        """
        Retrieves the TopicId associated with the transaction receipt, if available.

        Returns:
            TopicId or None: The TopicId if present; otherwise, None.
        """
        if self._receipt_proto.HasField("topicID") and self._receipt_proto.topicID.topicNum != 0:
            return TopicId._from_proto(self._receipt_proto.topicID)
        return None

    @property
    def account_id(self) -> AccountId | None:
        """
        Retrieves the AccountId associated with the transaction receipt, if available.

        Unlike other ID properties (token_id, file_id, etc.), this returns the AccountId
        even when accountNum is 0. This is intentional to support EVM auto-account creation
        scenarios where the protobuf may contain an AccountID with num=0 to identify the
        newly created account before it's fully initialized on-chain.

        Returns:
            AccountId or None: The AccountId if present (including num=0); otherwise, None.
        """
        if self._receipt_proto.HasField("accountID"):
            return AccountId._from_proto(self._receipt_proto.accountID)
        return None

    @property
    def serial_numbers(self) -> list[int]:
        """
        Retrieves the serial numbers associated with the transaction receipt, if available.

        Returns:
            list of int: The serial numbers if present; otherwise, an empty list.
        """
        return cast(list[int], self._receipt_proto.serialNumbers)

    @property
    def file_id(self) -> FileId | None:
        """
        Returns the file ID associated with this receipt.
        """
        if self._receipt_proto.HasField("fileID") and self._receipt_proto.fileID.fileNum != 0:
            return FileId._from_proto(self._receipt_proto.fileID)
        return None

    @property
    def transaction_id(self) -> TransactionId | None:
        """
        Returns the transaction ID associated with this receipt.

        Returns:
            TransactionId: The transaction ID.
        """
        return self._transaction_id

    @property
    def contract_id(self):
        """
        Returns the contract ID associated with this receipt.

        Returns:
            ContractId or None: The ContractId if present; otherwise, None.
        """
        if self._receipt_proto.HasField("contractID") and self._receipt_proto.contractID.contractNum != 0:
            return ContractId._from_proto(self._receipt_proto.contractID)

        return None

    @property
    def schedule_id(self):
        """
        Returns the schedule ID associated with this receipt.

        Returns:
            ScheduleId or None: The ScheduleId if present; otherwise, None.
        """
        if self._receipt_proto.HasField("scheduleID") and self._receipt_proto.scheduleID.scheduleNum != 0:
            return ScheduleId._from_proto(self._receipt_proto.scheduleID)

        return None

    @property
    def scheduled_transaction_id(self):
        """
        Returns the schedule transaction ID associated with this receipt.

        Returns:
            TransactionId or None: The TransactionId if present; otherwise, None.
        """
        if self._receipt_proto.HasField("scheduledTransactionID"):
            return TransactionId._from_proto(self._receipt_proto.scheduledTransactionID)

        return None

    @property
    def node_id(self):
        """
        Returns the node ID associated with this receipt.

        Returns:
            int: The node ID if present; otherwise, 0.
        """
        return self._receipt_proto.node_id

    @property
    def registered_node_id(self) -> int | None:
        """
        Returns the registered node ID associated with this receipt.

        Returns:
            int | None: The registered node ID if present; otherwise, None.
        """
        if self._receipt_proto.registered_node_id == 0:
            return None
        return self._receipt_proto.registered_node_id

    @property
    def topic_sequence_number(self) -> int:
        """
        Returns the topic sequence number associated with this receipt.

        Returns:
            int: The sequence number of the topic if present, otherwise 0.
        """
        return self._receipt_proto.topicSequenceNumber

    @property
    def topic_running_hash(self) -> bytes | None:
        """
        Returns the topic running hash associated with this receipt.

        Returns:
            int: The running hash of the topic if present, otherwise None.
        """
        if self._receipt_proto.HasField("topicRunningHash"):
            return self._receipt_proto.topicRunningHash

        return None

    @property
    def children(self) -> list[TransactionReceipt]:
        """
        Returns the child transaction receipts associated with this receipt.

        Returns:
            list[TransactionReceipt]: Child receipts (empty if not requested or none exist).
        """
        return self._children

    def _set_children(self, children: list[TransactionReceipt]) -> None:
        """
        Internal setter for child receipts (used by receipt queries).

        Args:
            children (list[TransactionReceipt]): Child receipts.
        """
        self._children = children

    @property
    def duplicates(self) -> list[TransactionReceipt]:
        """
        Returns the duplicate transaction receipts associated with this receipt.

        Returns:
            list[TransactionReceipt]: Duplicate receipts (empty if not requested or none exist).
        """
        return self._duplicates

    def _set_duplicates(self, duplicates: list[TransactionReceipt]) -> None:
        """
        Internal setter for duplicate receipts (used by receipt queries).

        Args:
            duplicates (list[TransactionReceipt]): Duplicate receipts.
        """
        self._duplicates = duplicates

    def _to_proto(self):
        """
        Returns the underlying protobuf transaction receipt.

        Returns:
            transaction_receipt_pb2.TransactionReceipt: The protobuf transaction receipt.
        """
        return self._receipt_proto

    @classmethod
    def _from_proto(
        cls, proto: transaction_receipt_pb2.TransactionReceipt, transaction_id: TransactionId | None
    ) -> TransactionReceipt:
        """
        Creates a TransactionReceipt instance from a protobuf TransactionReceipt object.

        Args:
            proto (transaction_receipt_pb2.TransactionReceipt): The protobuf TransactionReceipt object.
            transaction_id (TransactionId | None): The transaction ID associated with this receipt. Can be None for child receipts.

        Returns:
            TransactionReceipt: A new instance of TransactionReceipt populated with data from the protobuf object.
        """
        return cls(receipt_proto=proto, transaction_id=transaction_id)
