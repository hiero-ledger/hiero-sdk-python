"""Response model for fee estimation results.

Contains the calculated fees across different categories along with
the estimation mode and optional notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.fees.fee_estimate import FeeEstimate
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.fees.network_fee import NetworkFee


@dataclass(frozen=True)
class FeeEstimateResponse:
    """Represents the result of a fee estimation operation."""

    mode: FeeEstimateMode
    network_fee: NetworkFee | None = None
    node_fee: FeeEstimate | None = None
    service_fee: FeeEstimate | None = None
    notes: list[str] = field(default_factory=list)
    total: int = 0
