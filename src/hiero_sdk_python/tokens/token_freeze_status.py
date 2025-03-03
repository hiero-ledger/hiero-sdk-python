from enum import Enum

class TokenFreezeStatus(Enum):
    FREEZE_NOT_APPLICABLE = 0
    FROZEN = 1
    UNFROZEN = 2