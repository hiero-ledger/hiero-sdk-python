from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkFee:
    multiplier: int
    subtotal: int
