from enum import Enum
from typing import Any
from hiero_sdk_python.hapi.services import basic_types_pb2

"""
TokenKeyValidation specifies whether token key validation should be performed during transaction processing.
FULL_VALIDATION means all token key validation checks will be performed.
NO_VALIDATION means token key validation checks will be skipped.
"""
class TokenKeyValidation(Enum):
    FULL_VALIDATION = 0
    NO_VALIDATION = 1

    @staticmethod
    def _from_proto(proto_obj: basic_types_pb2.TokenKeyValidation) -> "TokenKeyValidation":
        """Converts a proto TokenKeyValidation object to a TokenKeyValidation enum."""
        if proto_obj == basic_types_pb2.TokenKeyValidation.FULL_VALIDATION:
            return TokenKeyValidation.FULL_VALIDATION
        elif proto_obj == basic_types_pb2.TokenKeyValidation.NO_VALIDATION:
            return TokenKeyValidation.NO_VALIDATION
        
    def _to_proto(self) -> basic_types_pb2.TokenKeyValidation:
        """Converts a TokenKeyValidation enum to a proto TokenKeyValidation object."""
        if self == TokenKeyValidation.FULL_VALIDATION:
            return basic_types_pb2.TokenKeyValidation.FULL_VALIDATION
        elif self == TokenKeyValidation.NO_VALIDATION:
            return basic_types_pb2.TokenKeyValidation.NO_VALIDATION

    def __eq__(self, other: Any) -> bool:
        """Checks equality with another TokenKeyValidation or an integer."""
        if isinstance(other, TokenKeyValidation):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other