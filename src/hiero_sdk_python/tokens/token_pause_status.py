from enum import Enum
from typing import Any
from hiero_sdk_python.hapi.services import basic_types_pb2

"""
A Token's paused status shows whether or not a Token can be used or not in a transaction.
"""
class TokenPauseStatus(Enum):
    PAUSE_NOT_APPLICABLE = 0
    PAUSED = 1
    UNPAUSED = 2

    @staticmethod
    def _from_proto(proto_obj: basic_types_pb2.TokenPauseStatus) -> "TokenPauseStatus":
        if proto_obj == basic_types_pb2.TokenPauseStatus.PauseNotApplicable:
            return TokenPauseStatus.PAUSE_NOT_APPLICABLE
        elif proto_obj == basic_types_pb2.TokenPauseStatus.Paused:
            return TokenPauseStatus.PAUSED
        elif proto_obj == basic_types_pb2.TokenPauseStatus.Unpaused:
            return TokenPauseStatus.UNPAUSED

    def __eq__(self, other: Any) -> bool:
        """
        Checks equality with another TokenPauseStatus or an integer value.
        Args:
            other (Any): The object to compare with.
        Returns:
            bool: True if the values are equal, False otherwise.
        """
        if isinstance(other, TokenPauseStatus):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other