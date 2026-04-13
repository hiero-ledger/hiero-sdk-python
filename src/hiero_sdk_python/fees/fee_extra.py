from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class FeeExtra:
    name: Optional[str] = None
    included: Optional[int] = None
    count: Optional[int] = None
    charged: Optional[int] = None
    fee_per_unit: Optional[int] = None
    subtotal: Optional[int] = None