from enum import Enum

class TokenKycStatus(Enum):
    KYC_NOT_APPLICABLE = 0
    GRANTED = 1
    REVOKED = 2