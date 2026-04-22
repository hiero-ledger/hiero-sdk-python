"""Fee estimation models for calculating base and extra fees.

This module defines the FeeEstimate dataclass, which aggregates
a base fee with optional extra fee components.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.fees.fee_extra import FeeExtra


@dataclass(frozen=True)
class FeeEstimate:
    """Represents a fee estimate composed of a base amount and optional extras."""

    base: int
    # extras: list[FeeExtra] = field(default_factory=list)
    extras: tuple[FeeExtra, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extras", tuple(self.extras))

    @property
    def subtotal(self) -> int:
        """Return the total fee including base and all extras."""
        return self.base + sum(extra.subtotal or 0 for extra in self.extras)
        # return self.base + sum(extra.subtotal for extra in self.extras)
