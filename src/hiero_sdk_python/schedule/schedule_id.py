"""
ScheduleId class.
"""

from dataclasses import dataclass

from hiero_sdk_python.hapi.services.basic_types_pb2 import ScheduleID as ProtoScheduleID


@dataclass(frozen=True)
class ScheduleId:
    """
    Represents the unique identifier for a schedule.

    A schedule ID consists of three components: shard, realm, and schedule.
    These components uniquely identify a schedule in the network.

    Attributes:
        shard (int): The shard number. Defaults to 0.
        realm (int): The realm number. Defaults to 0.
        schedule (int): The unique schedule number within the shard/realm. Defaults to 0.
    """

    shard: int = 0
    realm: int = 0
    schedule: int = 0

    @classmethod
    def from_string(cls, id_str: str) -> "ScheduleId":
        """
        Creates a ScheduleId instance from a string representation.

        Parses a string in the format 'shard.realm.schedule' into a ScheduleId object.
        All three components must be present and be valid non-negative integers.

        Args:
            id_str (str): The string representation of the schedule ID in the format
                'shard.realm.schedule'. Leading/trailing whitespace is automatically stripped.

        Returns:
            ScheduleId: A new ScheduleId instance with the parsed components.

        Raises:
            ValueError: If the string is not in the correct format, doesn't contain
                exactly 3 dot-separated components, or contains non-integer values.
        """
        try:
            shard_str, realm_str, schedule_str = id_str.strip().split(".")
            return cls(
                shard=int(shard_str),
                realm=int(realm_str),
                schedule=int(schedule_str),
            )
        except Exception as e:
            raise ValueError(
                f"Invalid schedule ID string '{id_str}'. Expected format 'shard.realm.schedule'."
            ) from e

    def __str__(self) -> str:
        """
        Returns the string representation of the schedule ID.

        Returns:
            str: The formatted schedule ID string in 'shard.realm.schedule' format.
        """
        return f"{self.shard}.{self.realm}.{self.schedule}"

    def __repr__(self) -> str:
        """
        Returns the detailed string representation of the schedule ID for debugging.

        Returns a representation that shows the class name and all component values,
        which is useful for debugging and development purposes.

        Returns:
            str: A detailed representation in the format
                'ScheduleId(shard=X, realm=Y, schedule=Z)'.
        """
        return f"ScheduleId(shard={self.shard}, realm={self.realm}, schedule={self.schedule})"

    def __eq__(self, other: object) -> bool:
        """
        Checks equality between two ScheduleId instances.

        Args:
            other (object): The object to compare with. Must be a ScheduleId instance
                for equality to be possible.

        Returns:
            bool: True if both instances are ScheduleId objects with identical
                shard, realm, and schedule values, False otherwise.
        """
        if not isinstance(other, ScheduleId):
            return NotImplemented
        return (
            self.shard == other.shard
            and self.realm == other.realm
            and self.schedule == other.schedule
        )

    def _to_proto(self) -> ProtoScheduleID:
        """
        Converts the ScheduleId instance to a protobuf ScheduleID object.

        Returns:
            ProtoScheduleID: The protobuf ScheduleID object with the same
                shard, realm, and schedule values.

        Note:
            This is an internal method and should not be used directly by client code.
        """
        return ProtoScheduleID(
            shardNum=self.shard,
            realmNum=self.realm,
            scheduleNum=self.schedule,
        )

    @classmethod
    def _from_proto(cls, proto: ProtoScheduleID) -> "ScheduleId":
        """
        Creates a ScheduleId instance from a protobuf ScheduleID object.

        This is an internal method used for deserialization when receiving responses
        from the Hedera network via gRPC. It handles the conversion from the protobuf
        field names (shardNum, realmNum, scheduleNum) to the Python representation.

        Args:
            proto (ProtoScheduleID): The protobuf ScheduleID object to convert.

        Returns:
            ScheduleId: A new ScheduleId instance with the values from the protobuf object.
        """
        return cls(
            shard=proto.shardNum, realm=proto.realmNum, schedule=proto.scheduleNum
        )
