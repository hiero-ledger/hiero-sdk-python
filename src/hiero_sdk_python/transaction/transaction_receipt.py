from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.account.account_id import AccountId


class TransactionReceipt:
    """
    Represents the receipt of a transaction.

    The receipt contains information about the status and result of a transaction,
    such as the TokenId or AccountId involved.

    Attributes:
        status (ResponseCode): The status code of the transaction.
        _receipt_proto (TransactionReceiptProto): The underlying protobuf receipt.
    """

    def __init__(self, receipt_proto, transaction_id=None):
        """
        Initializes the TransactionReceipt with the provided protobuf receipt.

        Args:
            receipt_proto (TransactionReceiptProto): The protobuf transaction receipt.
        """
        self._transaction_id = transaction_id
        self.status = receipt_proto.status
        self._receipt_proto = receipt_proto

    @property
    def tokenId(self):
        """
        Retrieves the TokenId associated with the transaction receipt, if available.

        Returns:
            TokenId or None: The TokenId if present; otherwise, None.
        """
        if self._receipt_proto.HasField('tokenID') and self._receipt_proto.tokenID.tokenNum != 0:
            return TokenId._from_proto(self._receipt_proto.tokenID)
        else:
            return None

    @property
    def topicId(self):
        """
        Retrieves the TopicId associated with the transaction receipt, if available.

        Returns:
            TopicId or None: The TopicId if present; otherwise, None.
        """
        if self._receipt_proto.HasField('topicID') and self._receipt_proto.topicID.topicNum != 0:
            return TopicId._from_proto(self._receipt_proto.topicID)
        else:
            return None

    @property
    def accountId(self):
        """
        Retrieves the AccountId associated with the transaction receipt, if available.

        Returns:
            AccountId or None: The AccountId if present; otherwise, None.
        """
        if self._receipt_proto.HasField('accountID') and self._receipt_proto.accountID.accountNum != 0:
            return AccountId._from_proto(self._receipt_proto.accountID)
        else:
            return None

    @property
    def serial_numbers(self):
        """
        Retrieves the serial numbers associated with the transaction receipt, if available.
        
        Returns:
            list of int: The serial numbers if present; otherwise, an empty list.
        """
        return self._receipt_proto.serialNumbers

    @property
    def transaction_id(self):
        """
        Returns the transaction ID associated with this receipt.

        Returns:
            TransactionId: The transaction ID.
        """
        return self._transaction_id

    def _to_proto(self):
        """
        Returns the underlying protobuf transaction receipt.

        Returns:
            TransactionReceiptProto: The protobuf transaction receipt.
        """
        return self._receipt_proto

    @classmethod
    def _from_proto(cls, proto, transaction_id=None):
        return cls(receipt_proto=proto, transaction_id=transaction_id)
