"""
hiero_sdk_python.tokens.token_key_validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenKeyValidation enum to control whether token key validation checks
are performed during Hedera transaction processing.
"""
from enum import Enum
from hiero_sdk_python.hapi.services.basic_types_pb2 import (
    TokenKeyValidation as proto_TokenKeyValidation,
)

class TokenKeyValidation(Enum):
    """
    Enum for token key validation modes:

      • FULL_VALIDATION – perform all validation checks  
      • NO_VALIDATION   – skip validation checks
    """
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
