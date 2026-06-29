"""TCK response models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateTokenResponse:
    """Response payload for createToken."""

    tokenId: str | None = None
    status: str | None = None


@dataclass
class MintTokenResponse:
    """Response payload for mintToken."""

    newTotalSupply: str | None = None
    serialNumbers: list[str] | None = None
    status: str | None = None


@dataclass
class AssociateTokenResponse(StatusOnlyResponse):
    """Response payload for associateToken."""


@dataclass
class DeleteTokenResponse(StatusOnlyResponse):
    """Response payload for deleteToken."""


@dataclass
class FreezeTokenResponse(StatusOnlyResponse):
    """Response payload for freezeToken."""


@dataclass
class PauseTokenResponse(StatusOnlyResponse):
    """Response payload for pauseToken."""


@dataclass
class AirdropTokenResponse(StatusOnlyResponse):
    """Response payload for airdropToken."""
