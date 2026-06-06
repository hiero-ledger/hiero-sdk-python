"""TCK response models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass


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
class AssociateTokenResponse:
    """Response payload for associateToken."""

    status: str | None = None


@dataclass
class DeleteTokenResponse:
    """Response payload for deleteToken."""

    status: str | None = None


@dataclass
class FreezeTokenResponse:
    """Response payload for freezeToken."""

    status: str | None = None


@dataclass
class PauseTokenResponse:
    """Response payload for pauseToken."""

    status: str | None = None
