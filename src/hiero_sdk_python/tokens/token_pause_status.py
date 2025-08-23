"""
hiero_sdk_python.tokens.token_pause_status.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenPauseStatus enum for representing token pause states:
not applicable, paused, or unpaused.
A Token's paused status shows whether or not a Token can be used or not in a transaction.
"""
from enum import Enum
from typing import Any
from hiero_sdk_python.hapi.services import basic_types_pb2

class TokenPauseStatus(Enum):
    """
    Enumeration of token pause statuses:

      • PAUSE_NOT_APPLICABLE – pause not relevant  
      • PAUSED              – token is paused  
      • UNPAUSED            – token is active
    """
    PAUSE_NOT_APPLICABLE = 0
    PAUSED = 1
    UNPAUSED = 2

    @staticmethod
    def _from_proto(proto_obj: basic_types_pb2.TokenPauseStatus) -> "TokenPauseStatus":
        """
        Converts a protobuf TokenPauseStatus to a TokenPauseStatus enum.
        Args:
            proto_obj (basic_types_pb2.TokenPauseStatus): The protobuf TokenPauseStatus object.
        Returns:
            TokenPauseStatus: The corresponding TokenPauseStatus enum value.
        Raises:
            ValueError: If the proto object does not match any known TokenPauseStatus.
        """
        if proto_obj == basic_types_pb2.TokenPauseStatus.PauseNotApplicable:
            return TokenPauseStatus.PAUSE_NOT_APPLICABLE
        if proto_obj == basic_types_pb2.TokenPauseStatus.Paused:
            return TokenPauseStatus.PAUSED
        if proto_obj == basic_types_pb2.TokenPauseStatus.Unpaused:
            return TokenPauseStatus.UNPAUSED
        raise ValueError(f"Unknown TokenPauseStatus proto value: {proto_obj}")

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
        if isinstance(other, int):
            return self.value == other
        return False
