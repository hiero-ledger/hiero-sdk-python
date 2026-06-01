"""TCK response models for approveAllowance endpoint."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApproveAllowanceResponse:
    """Response payload for approveAllowance."""

    status: str | None = None
