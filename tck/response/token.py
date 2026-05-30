"""TCK response models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateTokenResponse:
    """Response payload for createToken."""

    tokenId: str | None = None
    status: str | None = None
