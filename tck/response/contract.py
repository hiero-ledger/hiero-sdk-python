from __future__ import annotations

from dataclasses import dataclass

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateContractResponse:
    """Response payload for createContract."""

    contractId: str | None = None
    status: str | None = None


@dataclass
class UpdateContractResponse(StatusOnlyResponse):
    """Response payload for updateContract."""
