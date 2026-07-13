"""TCK response models for allowance endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.response.base import StatusOnlyResponse


@dataclass
class ApproveAllowanceResponse(StatusOnlyResponse):
    """Response payload for approveAllowance."""


@dataclass
class DeleteAllowanceResponse(StatusOnlyResponse):
    """Response payload for deleteAllowance."""
