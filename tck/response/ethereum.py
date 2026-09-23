from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateEthereumTransactionResponse:
    """Response payload for createEthereumTransaction."""

    contractId: str | None = None
    status: str | None = None
