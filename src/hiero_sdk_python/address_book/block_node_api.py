from __future__ import annotations

from enum import IntEnum


class BlockNodeApi(IntEnum):
    """Maps to the BlockNodeApi enum defined inside RegisteredServiceEndpoint.BlockNodeEndpoint."""

    OTHER = 0
    STATUS = 1
    PUBLISH = 2
    SUBSCRIBE_STREAM = 3
    STATE_PROOF = 4
