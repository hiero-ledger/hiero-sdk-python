from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TransferCryptoResponse:
    status: str | None = None
