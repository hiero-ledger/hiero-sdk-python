from enum import Enum
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKycStatus as proto_TokenKycStatus

"""
KYC (Know Your Customer) Status indicates whether or not a person or entity has completed a verification of identity.
"""
class TokenKycStatus(Enum):
    KYC_NOT_APPLICABLE = 0
    GRANTED = 1
    REVOKED = 2

    @staticmethod
    def _from_proto(proto_obj: proto_TokenKycStatus):
        if proto_obj == proto_TokenKycStatus.KycNotApplicable:
            return TokenKycStatus.KYC_NOT_APPLICABLE
        elif proto_obj == proto_TokenKycStatus.Granted:
            return TokenKycStatus.GRANTED
        elif proto_obj == proto_TokenKycStatus.Revoked:
            return TokenKycStatus.REVOKED

    def __eq__(self, other):
        if isinstance(other, TokenKycStatus):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other