"""
transaction_receipt.py
~~~~~~~~~~~~~~~~~~~~~~

Defines the TransactionReceipt class, which represents the outcome of a Hedera transaction.

This module provides structured access to fields in a transaction receipt,
including associated IDs like TokenId, TopicId, AccountId, and FileId.
It wraps the underlying protobuf object and exposes key properties with
optional deprecated alias support via `_DeprecatedAliasesMixin`.

Classes:
    - TransactionReceipt: Parses and exposes fields from a transaction receipt protobuf.
"""
from typing import Optional, cast
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python._deprecated import _DeprecatedAliasesMixin
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.hapi.services import transaction_receipt_pb2, response_code_pb2

class TransactionReceipt(_DeprecatedAliasesMixin):  # type: ignore[misc]
    """
    Represents the receipt of a transaction.
    Imports deprecated aliases for tokenId, topicId and accountId.

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
        transaction_id: Optional[TransactionId] = None
    ) -> None:
        """
        Initializes the TransactionReceipt with the provided protobuf receipt.

        Args:
            receipt_proto (transaction_receipt_pb2.TransactionReceiptProto, optional): The protobuf transaction receipt.
            transaction_id (TransactionId, optional): The transaction ID associated with this receipt.
        """
        self._transaction_id: Optional[TransactionId] = transaction_id
        self.status: Optional[response_code_pb2.ResponseCodeEnum] = receipt_proto.status
        self._receipt_proto: transaction_receipt_pb2.TransactionReceipt = receipt_proto

    @property
    def token_id(self) -> Optional[TokenId]:
        """
        Retrieves the TokenId associated with the transaction receipt, if available.

        Returns:
            TokenId or None: The TokenId if present; otherwise, None.
        """
        if self._receipt_proto.HasField('tokenID') and self._receipt_proto.tokenID.tokenNum != 0:
            return TokenId._from_proto(self._receipt_proto.tokenID)
        return None

    @property
    def topic_id(self) -> Optional[TopicId]:
        """
        Retrieves the TopicId associated with the transaction receipt, if available.

        Returns:
            TopicId or None: The TopicId if present; otherwise, None.
        """
        if self._receipt_proto.HasField('topicID') and self._receipt_proto.topicID.topicNum != 0:
            return TopicId._from_proto(self._receipt_proto.topicID)
        return None

    @property
    def account_id(self) -> Optional[AccountId]:
        """
        Retrieves the AccountId associated with the transaction receipt, if available.

        Returns:
            AccountId or None: The AccountId if present; otherwise, None.
        """
        if (
            self._receipt_proto.HasField('accountID')
            and self._receipt_proto.accountID.accountNum != 0
        ):
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
    def file_id(self) -> Optional[FileId]:
        """
        Returns the file ID associated with this receipt.
        """
        if self._receipt_proto.HasField('fileID') and self._receipt_proto.fileID.fileNum != 0:
            return FileId._from_proto(self._receipt_proto.fileID)
        return None

    @property
    def transaction_id(self) -> Optional[TransactionId]:
        """
        Returns the transaction ID associated with this receipt.

        Returns:
            TransactionId: The transaction ID.
        """
        return self._transaction_id

    def _to_proto(self) -> transaction_receipt_pb2.TransactionReceipt:
        """
        Returns the underlying protobuf transaction receipt.

        Returns:
            transaction_receipt_pb2.TransactionReceipt: The protobuf transaction receipt.
        """
        return self._receipt_proto

    @classmethod
    def _from_proto(cls, proto: transaction_receipt_pb2.TransactionReceipt, transaction_id: TransactionId) -> "TransactionReceipt":
        """
        Creates a TransactionReceipt instance from a protobuf TransactionReceipt object.
        Args:
            proto (transaction_receipt_pb2.TransactionReceipt): The protobuf TransactionReceipt object.
            transaction_id (TransactionId): The transaction ID associated with this receipt.
        Returns:
            TransactionReceipt: A new instance of TransactionReceipt populated with data from the protobuf object.
        """
        return cls(receipt_proto=proto, transaction_id=transaction_id)
