"""
This module defines data structures related to additional fee components.

It provides the `FeeExtra` data class, which represents optional and
extended fee information associated with transactions or operations.
These structures are used to capture detailed breakdowns of fees such as
per-unit costs, totals, and inclusion flags for billing or estimation purposes.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class FeeExtra:
    """
    Represents additional fee details associated with a transaction or operation.

    This data class captures optional metadata about an extra fee component,
    including its name, inclusion status, quantity, charged amount, per-unit fee,
    and computed subtotal.

    Attributes:
        name: The name or label of the fee component.
        included: Indicates whether the fee is included (typically 0/1 or boolean-like int).
        count: The number of units or occurrences contributing to the fee.
        charged: The total amount charged for this fee component.
        fee_per_unit: The fee applied per individual unit.
        subtotal: The computed subtotal for this fee component.
    """

    name: Optional[str] = None
    included: Optional[int] = None
    count: Optional[int] = None
    charged: Optional[int] = None
    fee_per_unit: Optional[int] = None
    subtotal: Optional[int] = None
