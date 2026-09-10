from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateContractResponse:
    """Response payload for createContract."""

    contractId: str | None = None
    status: str | None = None
