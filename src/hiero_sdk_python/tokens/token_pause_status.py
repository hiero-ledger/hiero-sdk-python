"""
hiero_sdk_python.tokens.token_pause_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenPauseStatus enum for representing token pause states:
not applicable, paused, or unpaused.
"""
from enum import Enum
from hiero_sdk_python.hapi.services.basic_types_pb2 import (
    TokenPauseStatus as proto_TokenPauseStatus,
)

"""
A Token's paused status shows whether or not a Token can be used or not in a transaction.
"""
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
    def _from_proto(proto_obj: proto_TokenPauseStatus):
        if proto_obj == proto_TokenPauseStatus.PauseNotApplicable:
            return TokenPauseStatus.PAUSE_NOT_APPLICABLE
        elif proto_obj == proto_TokenPauseStatus.Paused:
            return TokenPauseStatus.PAUSED
        elif proto_obj == proto_TokenPauseStatus.Unpaused:
            return TokenPauseStatus.UNPAUSED

    def __eq__(self, other):
        if isinstance(other, TokenPauseStatus):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
