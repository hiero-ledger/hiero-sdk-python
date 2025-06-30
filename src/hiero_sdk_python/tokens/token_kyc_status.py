from enum import Enum
from typing import Any
from hiero_sdk_python.hapi.services import basic_types_pb2

"""
KYC (Know Your Customer) Status indicates whether or not a person or entity has completed a verification of identity.
"""
class TokenKycStatus(Enum):
    KYC_NOT_APPLICABLE = 0
    GRANTED = 1
    REVOKED = 2

    @staticmethod
    def _from_proto(proto_obj: basic_types_pb2.TokenKycStatus) -> "TokenKycStatus":
        """Converts a proto TokenKycStatus object to a TokenKycStatus enum."""
        if proto_obj == basic_types_pb2.TokenKycStatus.KycNotApplicable:
            return TokenKycStatus.KYC_NOT_APPLICABLE
        elif proto_obj == basic_types_pb2.TokenKycStatus.Granted:
            return TokenKycStatus.GRANTED
        elif proto_obj == basic_types_pb2.TokenKycStatus.Revoked:
            return TokenKycStatus.REVOKED

    def __eq__(self, other: Any) -> bool:
        """Checks equality with another TokenKycStatus or an integer."""
        if isinstance(other, TokenKycStatus):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other