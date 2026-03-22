from dataclasses import dataclass

@dataclass(frozen=True)
class FeeExtra:
    name: str
    included: int
    count: int
    charged: int
    fee_per_unit: int
    subtotal: int