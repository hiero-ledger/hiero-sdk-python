from typing import Optional
import requests
import time
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.fees.fee_estimate_response import FeeEstimateResponse
from hiero_sdk_python.fees.fee_extra import FeeExtra
from hiero_sdk_python.fees.fee_estimate import FeeEstimate
from hiero_sdk_python.fees.network_fee import NetworkFee

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hiero_sdk_python.transaction.transaction import Transaction

class FeeEstimateQuery:

    def __init__(self):
        self._mode: Optional[FeeEstimateMode] = None
        self._transaction: Optional["Transaction"] = None
        self._max_attempts = 10
        self._max_backoff = 0

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

    def _backoff(self, attempt: int):
        delay = min(0.5 * (2 ** attempt), self._max_backoff)
        time.sleep(delay)
    
    def _ensure_frozen(self, tx, client):
        try:
            tx._require_frozen()
        except Exception:
            # fallback: fully prepare transaction before serialization
            if hasattr(tx, "freeze_with"):
                tx.freeze_with(client)
            else:
                tx.freeze()

    def set_max_attempts(self, attempts: int) -> "FeeEstimateQuery":
        self._max_attempts = attempts
        return self

    def get_max_attempts(self) -> int:
        return self._max_attempts

    def set_max_backoff(self, backoff: int) -> "FeeEstimateQuery":
        self._max_backoff = backoff
        return self

    def get_max_backoff(self) -> int:
        return self._max_backoff
    
    def execute(self, client) -> FeeEstimateResponse:
        if self._transaction is None:
            raise ValueError("Transaction must be set")

        mode = self._mode or FeeEstimateMode.STATE
        url = f"{client.mirror_network}/api/v1/network/fees?mode={mode.value}"

        tx = self._transaction

        if not tx._transaction_body_bytes:
            tx.freeze_with(client)
        
        try:
            tx_bytes = tx.to_bytes()
        except Exception:
            try:
                tx_bytes = tx.build_transaction_body().SerializeToString()
            except Exception:
                tx_bytes = b""  # fallback for incomplete tx

        node_total = 0
        service_total = 0
        network_multiplier = None
        notes = []
        
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    data=tx_bytes,
                    headers={"Content-Type": "application/protobuf"},
                    timeout=10,
                )

                if response.status_code == 400:
                    raise ValueError("Invalid argument")
                    
                break  # success → exit loop

            except Exception as e:
                message = str(e)

                if attempt == max_retries - 1:
                    raise  # out of retries

                if "UNAVAILABLE" in message or "DEADLINE_EXCEEDED" in message:
                    continue  # retry
                else:
                    raise  # non-retryable error

        network_multiplier = network_multiplier or 0
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