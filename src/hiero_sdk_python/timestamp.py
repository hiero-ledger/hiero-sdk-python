from datetime import datetime, timedelta, timezone
import random
import time

from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto


class Timestamp:
    """
    Represents a specific moment in time with nanosecond precision.
    """

    MAX_NS = 1_000_000_000

    def __init__(self, seconds: int, nanos: int):
        """
        Initialize a new `Timestamp` instance.

        Args:
            seconds (int): Number of seconds since epoch.
            nanos (int): Number of nanoseconds past the last second.
        """
        self.seconds = seconds
        self.nanos = nanos

    @staticmethod
    def generate(has_jitter=True) -> "Timestamp":
        """
        Generate a `Timestamp` with optional jitter.

        Args:
            has_jitter (bool): Whether to introduce random jitter. Default is True.

        Returns:
            Timestamp: A new `Timestamp` instance.
        """
        jitter = random.randint(3000, 8000) if has_jitter else 0
        now_ms = int(round(time.time() * 1000)) - jitter
        seconds = now_ms // 1000
        nanos = (now_ms % 1000) * 1_000_000 + random.randint(0, 999_999)

        return Timestamp(seconds, nanos)

    @staticmethod
    def from_date(date) -> "Timestamp":
        """
        Create a `Timestamp` from a Python `datetime` object, timestamp, or string.

        Args:
            date (datetime | int | str): A `datetime`, timestamp (int), or ISO 8601 string.

        Returns:
            Timestamp: A `Timestamp` instance.
        """
        if isinstance(date, datetime):
            seconds = int(date.timestamp())
            nanos = int((date.timestamp() % 1) * Timestamp.MAX_NS)
        elif isinstance(date, int):
            seconds = date
            nanos = 0
        elif isinstance(date, str):
            parsed_date = datetime.fromisoformat(date)
            seconds = int(parsed_date.timestamp())
            nanos = int((parsed_date.timestamp() % 1) * Timestamp.MAX_NS)
        else:
            raise ValueError("Invalid type for 'date'. Must be datetime, int, or str.")

        return Timestamp(seconds, nanos)

    def to_date(self) -> datetime:
        """
        Convert the `Timestamp` to a Python `datetime` object.

        Returns:
            datetime: A `datetime` instance.
        """
        return datetime.fromtimestamp(self.seconds, tz=timezone.utc) + timedelta(
            microseconds=self.nanos // 1000
        )

    def plus_nanos(self, nanos: int) -> "Timestamp":
        """
        Add nanoseconds to the current `Timestamp`.

        Args:
            nanos (int): The number of nanoseconds to add.

        Returns:
            Timestamp: A new `Timestamp` instance.
        """
        total_nanos = self.nanos + nanos
        new_seconds = self.seconds + total_nanos // Timestamp.MAX_NS
        new_nanos = total_nanos % Timestamp.MAX_NS

        return Timestamp(new_seconds, new_nanos)

    def _to_protobuf(self) -> TimestampProto:
        """
        Convert the `Timestamp` to corresponding protobuf object.

        Returns:
            dict: A protobuf representation of the `Timestamp`.
        """
        return TimestampProto(seconds=self.seconds, nanos=self.nanos)

    @staticmethod
    def _from_protobuf(pb_obj: TimestampProto) -> "Timestamp":
        """
        Create a `Timestamp` from a protobuf object.

        Args:
            pb_obj (timestamp_pb2.Timestamp): A protobuf Timestamp object.

        Returns:
            Timestamp: A `Timestamp` instance.
        """

        return Timestamp(pb_obj.seconds, pb_obj.nanos)

    def __str__(self) -> str:
        """
        Get a string representation of the `Timestamp`.

        Returns:
            str: The string representation in the format `seconds.nanos`.
        """
        return f"{self.seconds}.{str(self.nanos).zfill(9)}"

    def compare(self, other: "Timestamp") -> int:
        """
        Compare the current `Timestamp` with another.

        Args:
            other (Timestamp): The `Timestamp` to compare with.

        Returns:
            int: -1 if this `Timestamp` is earlier, 1 if later, 0 if equal.
        """
        if self.seconds != other.seconds:
            return -1 if self.seconds < other.seconds else 1
        if self.nanos != other.nanos:
            return -1 if self.nanos < other.nanos else 1
        return 0

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another object.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return False
        return self.seconds == other.seconds and self.nanos == other.nanos

    def __hash__(self) -> int:
        """
        Get the hash value of the `Timestamp`.

        Returns:
            int: The hash value.
        """
        return hash((self.seconds, self.nanos))
