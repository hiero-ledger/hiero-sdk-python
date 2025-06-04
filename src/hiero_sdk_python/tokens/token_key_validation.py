from enum import Enum
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKeyValidation as proto_TokenKeyValidation

"""
TokenKeyValidation specifies whether token key validation should be performed during transaction processing.
FULL_VALIDATION means all token key validation checks will be performed.
NO_VALIDATION means token key validation checks will be skipped.
"""
class TokenKeyValidation(Enum):
    FULL_VALIDATION = 0
    NO_VALIDATION = 1

    @staticmethod
    def _from_proto(proto_obj: proto_TokenKeyValidation):
        if proto_obj == proto_TokenKeyValidation.FULL_VALIDATION:
            return TokenKeyValidation.FULL_VALIDATION
        elif proto_obj == proto_TokenKeyValidation.NO_VALIDATION:
            return TokenKeyValidation.NO_VALIDATION
        
    def _to_proto(self):
        if self == TokenKeyValidation.FULL_VALIDATION:
            return proto_TokenKeyValidation.FULL_VALIDATION
        elif self == TokenKeyValidation.NO_VALIDATION:
            return proto_TokenKeyValidation.NO_VALIDATION

    def __eq__(self, other):
        if isinstance(other, TokenKeyValidation):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other