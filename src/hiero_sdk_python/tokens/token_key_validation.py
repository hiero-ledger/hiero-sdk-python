"""
hiero_sdk_python.tokens.token_key_validation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenKeyValidation enum to control whether token key validation checks
are performed during Hedera transaction processing.
"""
from enum import Enum
from typing import Any
from hiero_sdk_python.hapi.services import basic_types_pb2

class TokenKeyValidation(Enum):
    """
    Enum for token key validation modes:

      • FULL_VALIDATION – perform all validation checks  
      • NO_VALIDATION   – skip validation checks
    """
    FULL_VALIDATION = 0
    NO_VALIDATION = 1

    @staticmethod
    def _from_proto(proto_obj: basic_types_pb2.TokenKeyValidation) -> "TokenKeyValidation":
        """Converts a proto TokenKeyValidation object to a TokenKeyValidation enum."""
        if proto_obj == basic_types_pb2.TokenKeyValidation.FULL_VALIDATION:
            return TokenKeyValidation.FULL_VALIDATION
        if proto_obj == basic_types_pb2.TokenKeyValidation.NO_VALIDATION:
            return TokenKeyValidation.NO_VALIDATION
        raise ValueError(f"Unknown TokenKeyValidation proto value: {proto_obj}")

    def _to_proto(self) -> basic_types_pb2.TokenKeyValidation:
        """Converts a TokenKeyValidation enum to a proto TokenKeyValidation object."""
        if self == TokenKeyValidation.FULL_VALIDATION:
            return basic_types_pb2.TokenKeyValidation.FULL_VALIDATION
        if self == TokenKeyValidation.NO_VALIDATION:
            return basic_types_pb2.TokenKeyValidation.NO_VALIDATION
        raise ValueError(f"Unknown TokenKeyValidation value: {self.value}")

    def __eq__(self, other: Any) -> bool:
        """Checks equality with another TokenKeyValidation or an integer."""
        if isinstance(other, TokenKeyValidation):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return False
