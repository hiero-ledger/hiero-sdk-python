from __future__ import annotations

import secrets
import time
from typing import Any

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2


# Ranges of the protobuf Timestamp fields: seconds is an int64 and nanos is an int32.
_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1
_INT32_MIN, _INT32_MAX = -(2**31), 2**31 - 1


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
        account_id: AccountId | None = None,
        valid_start: timestamp_pb2.Timestamp | None = None,
        scheduled: bool = False,
    ) -> None:
        """
        Initializes a TransactionId with the given account ID and valid start timestamp.

        Args:
            account_id (AccountId, optional): The account ID initiating the transaction.
            valid_start (timestamp_pb2.Timestamp, optional): The valid start time of the transaction.
        """
        self.account_id: AccountId | None = account_id
        self.valid_start: timestamp_pb2.Timestamp | None = valid_start
        self.scheduled = scheduled

    @classmethod
    def generate(cls, account_id: AccountId) -> TransactionId:
        """
        Generates a new TransactionId using the current time as the valid start,
        subtracting a random number of seconds to adjust for potential network delays.

        Args:
            account_id (AccountId): The account ID initiating the transaction.

        Returns:
            TransactionId: A new TransactionId instance.
        """
        cut_off_seconds = secrets.choice([5, 6, 7, 8])
        adjusted_time: float = time.time() - cut_off_seconds
        seconds: int = int(adjusted_time)
        nanos: int = int((adjusted_time - seconds) * 1e9)
        valid_start = timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)
        return cls(account_id, valid_start, scheduled=False)

    @classmethod
    def from_string(cls, transaction_id_str: str) -> TransactionId:
        """
        Parses a TransactionId from a string in the format 'account_id@seconds.nanos[?scheduled]'.

        This method supports the optional '?scheduled' suffix. If present, the returned
        TransactionId will have its scheduled flag set to True. The method enforces
        strict validation on the format and any provided suffixes.

        Args:
            transaction_id_str (str): The string representation of the TransactionId
                                      (e.g., "0.0.123@1234567890.500" or "0.0.123@1234567890.500?scheduled").

        Returns:
            TransactionId: A new TransactionId instance.

        Raises:
            ValueError: If the input string is not in the correct format, contains an invalid
                suffix, or its seconds or nanos are not integers or are out of range
                (seconds must fit in a signed 64-bit integer and nanos in a signed 32-bit
                integer, as in the protobuf ``Timestamp``). The message names the part
                that failed.
        """
        if not isinstance(transaction_id_str, str):
            raise ValueError(f"Invalid TransactionId string format: {transaction_id_str}")

        original_string = transaction_id_str
        invalid_format = f"Invalid TransactionId string format: {original_string}"

        scheduled = False
        if "?" in transaction_id_str:
            transaction_id_str, suffix = transaction_id_str.split("?", 1)
            if suffix != "scheduled":
                raise ValueError(f"Invalid transaction ID suffix: ?{suffix}")
            scheduled = True

        if transaction_id_str.count("@") != 1:
            raise ValueError(invalid_format)
        account_id_str, timestamp_str = transaction_id_str.split("@")

        # Any failure to parse the account ID, including a warning raised as an error,
        # is reported as a format error.
        try:
            account_id = AccountId.from_string(account_id_str)
        except Exception as e:
            raise ValueError(invalid_format) from e

        if timestamp_str.count(".") != 1:
            raise ValueError(invalid_format)
        seconds_str, nanos_str = timestamp_str.split(".")

        seconds = cls._parse_timestamp_part(seconds_str, "seconds", _INT64_MIN, _INT64_MAX, invalid_format)
        nanos = cls._parse_timestamp_part(nanos_str, "nanos", _INT32_MIN, _INT32_MAX, invalid_format)

        valid_start = timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)
        return cls(account_id, valid_start, scheduled=scheduled)

    @staticmethod
    def _parse_timestamp_part(value: str, name: str, minimum: int, maximum: int, invalid_format: str) -> int:
        """
        Parses the seconds or nanos part of a transaction ID string.

        Args:
            value (str): The text of the part.
            name (str): The name of the part ("seconds" or "nanos"), used in error messages.
            minimum (int): The smallest allowed value.
            maximum (int): The largest allowed value.
            invalid_format (str): The generic error message for the whole string.

        Returns:
            int: The parsed value.

        Raises:
            ValueError: If the part is not an integer or is outside ``minimum``..``maximum``.
        """
        try:
            number = int(value)
        except ValueError as e:
            # int() also refuses very long digit strings (Python's integer string conversion
            # limit). Those are integers, just far outside the allowed range.
            if value.strip().lstrip("+-").isdigit():
                raise ValueError(f"{invalid_format} ({name} is out of range {minimum} to {maximum})") from e
            raise ValueError(f"{invalid_format} ({name} {value!r} is not a valid integer)") from e

        if not minimum <= number <= maximum:
            raise ValueError(f"{invalid_format} ({name} {number} is out of range {minimum} to {maximum})")

        return number

    def to_string(self) -> str:
        """
        Returns the string representation of the TransactionId in the format 'account_id@seconds.nanos'.

        Returns:
            str: The string representation of the TransactionId.
        """
        return f"{self.account_id}@{self.valid_start.seconds}.{self.valid_start.nanos}{'?scheduled' if self.scheduled else ''}"

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
        if self.scheduled:
            transaction_id_proto.scheduled = True
        return transaction_id_proto

    @classmethod
    def _from_proto(cls, transaction_id_proto: basic_types_pb2.TransactionID) -> TransactionId:
        """
        Creates a TransactionId instance from a protobuf TransactionID object.

        Args:
            transaction_id_proto (TransactionID): The protobuf TransactionID object.

        Returns:
            TransactionId: A new TransactionId instance.
        """
        account_id = AccountId._from_proto(transaction_id_proto.accountID)
        valid_start = transaction_id_proto.transactionValidStart
        scheduled = transaction_id_proto.scheduled
        return cls(account_id, valid_start, scheduled)

    def __eq__(self, other: Any) -> bool:
        """
        Checks if this TransactionId is equal to another.

        Args:
            other (TransactionId): The other TransactionId to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        return (
            isinstance(other, TransactionId)
            and self.account_id == other.account_id
            and self.valid_start.seconds == other.valid_start.seconds
            and self.valid_start.nanos == other.valid_start.nanos
            and self.scheduled == other.scheduled
        )

    def __hash__(self) -> int:
        """
        Returns the hash of the TransactionId.

        Returns:
            int: The hash value.
        """
        return hash((self.account_id, self.valid_start.seconds, self.valid_start.nanos, self.scheduled))

    def __str__(self) -> str:
        """
        Returns the string representation of the TransactionId.

        Returns:
            str: The string representation.
        """
        return self.to_string()
