from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeExtra:
    """
    Represents additional fee details associated with a transaction or operation.
    """

    name: str | None = None
    included: int | None = None
    count: int | None = None
    charged: int | None = None
    fee_per_unit: int | None = None
    subtotal: int | None = None
