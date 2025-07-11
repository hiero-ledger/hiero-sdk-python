import random
import time
from typing import Any, Optional
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2
from hiero_sdk_python.account.account_id import AccountId

class TransactionId:
    """
    Represents the unique identifier for a transaction.

    A TransactionId consists of an AccountId and a valid start timestamp.
    It ensures uniqueness for each transaction initiated by an account.

    Attributes:
        account_id (AccountId): The AccountId of the transaction's initiator.
        valid_start (Timestamp): The valid start time of the transaction.
    """

    def __init__(
        self, 
        account_id: Optional[AccountId] = None, 
        valid_start: Optional[timestamp_pb2.Timestamp] = None
    ) -> None:
        """
        Initializes a TransactionId with the given account ID and valid start timestamp.

        Args:
            account_id (AccountId, optional): The account ID initiating the transaction.
            valid_start (timestamp_pb2.Timestamp, optional): The valid start time of the transaction.
        """
        self.account_id: Optional[AccountId] = account_id
        self.valid_start: Optional[timestamp_pb2.Timestamp] = valid_start

    @classmethod
    def generate(cls, account_id: AccountId) -> "TransactionId":
        """
        Generates a new TransactionId using the current time as the valid start,
        subtracting a random number of seconds to adjust for potential network delays.

        Args:
            account_id (AccountId): The account ID initiating the transaction.

        Returns:
            TransactionId: A new TransactionId instance.
        """
        cut_off_seconds: int = random.randint(5, 8) # subtract random number of seconds between 5 and 8
        adjusted_time: float = time.time() - cut_off_seconds
        seconds: int = int(adjusted_time)
        nanos: int = int((adjusted_time - seconds) * 1e9)
        valid_start = timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)
        return cls(account_id, valid_start)

    @classmethod
    def from_string(cls, transaction_id_str: str) -> "TransactionId":
        """
        Parses a TransactionId from a string in the format 'account_id@seconds.nanos'.

        Args:
            transaction_id_str (str): The string representation of the TransactionId.

        Returns:
            TransactionId: A new TransactionId instance.

        Raises:
            ValueError: If the input string is not in the correct format.
        """
        try:
            account_id_str: Optional[str] = None
            timestamp_str: Optional[str] = None
            account_id_str, timestamp_str = transaction_id_str.split('@')
            account_id = AccountId.from_string(account_id_str)
            seconds_str, nanos_str = timestamp_str.split('.')
            valid_start = timestamp_pb2.Timestamp(seconds=int(seconds_str), nanos=int(nanos_str))
            return cls(account_id, valid_start)
        except Exception as e:
            raise ValueError(f"Invalid TransactionId string format: {transaction_id_str}") from e

    def to_string(self) -> str:
        """
        Returns the string representation of the TransactionId in the format 'account_id@seconds.nanos'.

        Returns:
            str: The string representation of the TransactionId.
        """
        return f"{self.account_id}@{self.valid_start.seconds}.{self.valid_start.nanos}"

    def _to_proto(self) -> basic_types_pb2.TransactionID:
        """
        Converts the TransactionId to its protobuf representation.

        Returns:
            TransactionID: The protobuf TransactionID object.
        """
        transaction_id_proto = basic_types_pb2.TransactionID()
        if self.account_id is not None:
            transaction_id_proto.accountID.CopyFrom(self.account_id._to_proto())
        if self.valid_start is not None:
            transaction_id_proto.transactionValidStart.CopyFrom(self.valid_start)
        return transaction_id_proto

    @classmethod
    def _from_proto(cls, transaction_id_proto: basic_types_pb2.TransactionID) -> "TransactionId":
        """
        Creates a TransactionId instance from a protobuf TransactionID object.

        Args:
            transaction_id_proto (TransactionID): The protobuf TransactionID object.

        Returns:
            TransactionId: A new TransactionId instance.
        """
        account_id = AccountId._from_proto(transaction_id_proto.accountID)
        valid_start = transaction_id_proto.transactionValidStart
        return cls(account_id, valid_start)

    def __eq__(self, other: Any) -> bool:
        """
        Checks if this TransactionId is equal to another.

        Args:
            other (TransactionId): The other TransactionId to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        return (
            isinstance(other, TransactionId) and
            self.account_id == other.account_id and
            self.valid_start.seconds == other.valid_start.seconds and
            self.valid_start.nanos == other.valid_start.nanos
        )

    def __hash__(self) -> int:
        """
        Returns the hash of the TransactionId.

        Returns:
            int: The hash value.
        """
        return hash((self.account_id, self.valid_start.seconds, self.valid_start.nanos))

    def __str__(self) -> str:
        """
        Returns the string representation of the TransactionId.

        Returns:
            str: The string representation.
        """
        return self.to_string()
