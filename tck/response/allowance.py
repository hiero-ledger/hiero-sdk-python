"""TCK response models for allowance endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApproveAllowanceResponse:
    """Response payload for approveAllowance."""

    status: str | None = None


@dataclass
class DeleteAllowanceResponse:
    """Response payload for deleteAllowance."""

    status: str | None = None
