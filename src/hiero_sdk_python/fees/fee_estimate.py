from dataclasses import dataclass, field
from typing import List
from .fee_extra import FeeExtra

@dataclass(frozen=True)
class FeeEstimate:
    base: int
    extras: List[FeeExtra] = field(default_factory=list)

    @property
    def subtotal(self) -> int:
        return self.base + sum(extra.subtotal for extra in self.extras)