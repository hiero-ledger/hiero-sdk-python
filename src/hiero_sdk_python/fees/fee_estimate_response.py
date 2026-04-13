"""Response model for fee estimation results.

Contains the calculated fees across different categories along with
the estimation mode and optional notes.
"""

from dataclasses import dataclass, field
from typing import Optional

from .fee_estimate import FeeEstimate
from .fee_estimate_mode import FeeEstimateMode
from .network_fee import NetworkFee


@dataclass(frozen=True)
class FeeEstimateResponse:
    """Represents the result of a fee estimation operation."""

    mode: FeeEstimateMode
    network_fee: Optional[NetworkFee] = None
    node_fee: Optional[FeeEstimate] = None
    service_fee: Optional[FeeEstimate] = None
    notes: list[str] = field(default_factory=list)
    total: int = 0
    