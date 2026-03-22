from dataclasses import dataclass, field
from typing import List
from .fee_estimate_mode import FeeEstimateMode
from .fee_estimate import FeeEstimate
from .network_fee import NetworkFee

@dataclass(frozen=True)
class FeeEstimateResponse:
    mode: FeeEstimateMode
    network_fee: NetworkFee
    node_fee: FeeEstimate
    service_fee: FeeEstimate
    notes: List[str] = field(default_factory=list)
    total: int = 0
    