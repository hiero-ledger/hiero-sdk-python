from dataclasses import dataclass, field
from typing import List, Optional
from .fee_estimate_mode import FeeEstimateMode
from .fee_estimate import FeeEstimate
from .network_fee import NetworkFee

@dataclass(frozen=True)
class FeeEstimateResponse:
    mode: FeeEstimateMode
    network_fee: Optional[NetworkFee] = None
    node_fee: Optional[FeeEstimate] = None
    service_fee: Optional[FeeEstimate] = None
    notes: List[str] = field(default_factory=list)
    total: int = 0
    