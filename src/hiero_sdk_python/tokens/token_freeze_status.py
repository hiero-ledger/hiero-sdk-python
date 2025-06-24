from enum import Enum
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenFreezeStatus as proto_TokenFreezeStatus

"""
TokenFreezeStatus shows whether or not an account can use a token in transactions.
"""
class TokenFreezeStatus(Enum):
    FREEZE_NOT_APPLICABLE = 0
    FROZEN = 1
    UNFROZEN = 2

    @staticmethod
    def _from_proto(proto_obj: proto_TokenFreezeStatus):
        if proto_obj == proto_TokenFreezeStatus.FreezeNotApplicable:
            return TokenFreezeStatus.FREEZE_NOT_APPLICABLE
        elif proto_obj == proto_TokenFreezeStatus.Frozen:
            return TokenFreezeStatus.FROZEN
        elif proto_obj == proto_TokenFreezeStatus.Unfrozen:
            return TokenFreezeStatus.UNFROZEN

    def __eq__(self, other):
        if isinstance(other, TokenFreezeStatus):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other