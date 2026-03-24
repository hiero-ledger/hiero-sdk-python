from typing import Optional
import requests
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.fees.fee_estimate_response import FeeEstimateResponse
from hiero_sdk_python.fees.fee_extra import FeeExtra
from hiero_sdk_python.fees.fee_estimate import FeeEstimate
from hiero_sdk_python.fees.network_fee import NetworkFee
from hiero_sdk_python.fees.fee_estimate_response import FeeEstimateResponse

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hiero_sdk_python.transaction.transaction import Transaction

class FeeEstimateQuery:

    def __init__(self):
        self._mode: Optional[FeeEstimateMode] = None
        self._transaction: Optional["Transaction"] = None

    def set_mode(self, mode: FeeEstimateMode) -> "FeeEstimateQuery":
        self._mode = mode 
        return self

    def get_mode(self) -> Optional[FeeEstimateMode]:
        return self._mode

    def set_transaction(self, transaction: "Transaction") -> "FeeEstimateQuery":

        #if hasattr(transaction, "freeze") and not transaction.is_frozen:
            #transaction.freeze()

        #if hasattr(transaction, "freeze") and not getattr(transaction, "is_frozen", False):
            #transaction.freeze()

        self._transaction = transaction
        return self

    def get_transaction(self) -> Optional["Transaction"]:
        return self._transaction
    
    def execute(self, client) -> FeeEstimateResponse:
        if self._transaction is None:
            raise ValueError("Transaction must be set")

        mode = self._mode or FeeEstimateMode.STATE

        url = f"{client.mirror_network}/api/v1/network/fees?mode={mode.value}"

        transactions = [b"dummy"]

        if not isinstance(transactions, list):
            transactions = [transactions]

        node_total = 0
        service_total = 0
        network_multiplier = None
        notes = []

        max_retries = getattr(client, "max_retries", 3)

        for tx in transactions:

            tx_bytes = b"dummy"
            for attempt in range(max_retries):

                try:

                    response = requests.post(
                        url,
                        data=tx_bytes,
                        headers={"Content-Type": "application/protobuf"},
                        timeout=10,
                    )

                    if response.status_code == 400:
                        raise ValueError("INVALID_ARGUMENT")

                    response.raise_for_status()

                    data = response.json()

                    parsed = self._parse_response(data)

                    node_total += parsed.node_fee.subtotal
                    service_total += parsed.service_fee.subtotal

                    network_multiplier = parsed.network_fee.multiplier
                    notes.extend(parsed.notes)

                    break
                except Exception as e:

                    if "UNAVAILABLE" in str(e) or "DEADLINE_EXCEEDED" in str(e):
                        if attempt == max_retries - 1:
                            raise
                        continue

                    raise

        network_total = node_total * network_multiplier
        total = node_total + service_total + network_total

        return FeeEstimateResponse(
            mode=mode,
            node_fee=FeeEstimate(base=node_total, extras=[]),
            service_fee=FeeEstimate(base=service_total, extras=[]),
            network_fee=NetworkFee(
                multiplier=network_multiplier,
                subtotal=network_total
            ),
            notes=notes,
            total=total
        )

    def _parse_response(self, data):

        node_fee = FeeEstimate(
            base=data["node"]["subtotal"],
            extras=[]
        )

        service_fee = FeeEstimate(
            base=data["service"]["subtotal"],
            extras=[]
        )

        network_fee = NetworkFee(
            multiplier=data["network"]["multiplier"],
            subtotal=0  # computed later
        )

        return FeeEstimateResponse(
            mode=FeeEstimateMode(data["mode"]),
            network_fee=network_fee,
            node_fee=node_fee,
            service_fee=service_fee,
            notes=data.get("notes", []),
            total=0,  # computed later
        )