"""
Fee estimation query module.

Provides `FeeEstimateQuery`, a mirror-node-backed query that estimates
transaction fees without submitting the transaction to the network.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import requests

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.fees.fee_estimate import FeeEstimate
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.fees.fee_estimate_response import FeeEstimateResponse
from hiero_sdk_python.fees.fee_extra import FeeExtra
from hiero_sdk_python.fees.network_fee import NetworkFee


if TYPE_CHECKING:
    from hiero_sdk_python.transaction.transaction import Transaction

logger = logging.getLogger(__name__)


class FeeEstimateQuery:
    """
    Query for estimating transaction fees via the mirror node REST API.

    This query sends a serialized HAPI transaction to
    `/api/v1/network/fees` and returns a structured
    `FeeEstimateResponse` containing node, service, and network fees.

    Key behaviors:
    - Defaults to INTRINSIC mode unless explicitly set
    - Automatically freezes transactions before execution
    - Retries transient failures (HTTP 500/503, timeouts)
    - Aggregates fees for internally chunked transactions
    """

    def __init__(self) -> None:
        self._mode: FeeEstimateMode | None = None
        self._transaction: Transaction | None = None
        self._high_volume_throttle: int = 0
        self._max_attempts: int = 3
        self._max_backoff: float = 2.0

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def set_mode(self, mode: FeeEstimateMode) -> FeeEstimateQuery:
        """Set the estimation mode (STATE or INTRINSIC)."""
        if not isinstance(mode, FeeEstimateMode):
            raise TypeError("mode must be a FeeEstimateMode")
        self._mode = mode
        return self

    def get_mode(self) -> FeeEstimateMode | None:
        """Return the configured estimation mode."""
        return self._mode

    def set_transaction(self, transaction: Transaction) -> FeeEstimateQuery:
        """Attach the transaction to estimate."""
        from hiero_sdk_python.transaction.transaction import Transaction

        if not isinstance(transaction, Transaction):
            raise TypeError(f"transaction must be an instance of Transaction, got {type(transaction).__name__}")
        self._transaction = transaction
        return self

    def get_transaction(self) -> Transaction | None:
        """Return the attached transaction."""
        return self._transaction

    def set_high_volume_throttle(self, high_volume_throttle: int) -> FeeEstimateQuery:
        """Set high-volume throttle utilization in basis points (0-10000, where 10000 = 100%)."""
        if not isinstance(high_volume_throttle, int):
            raise TypeError("high_volume_throttle must be an integer")

        if high_volume_throttle < 0 or high_volume_throttle > 10000:
            raise ValueError("high_volume_throttle must be between 0 and 10000")

        self._high_volume_throttle = high_volume_throttle
        return self

    def get_high_volume_throttle(self) -> int:
        """Return high-volume throttle utilization in basis points."""
        return self._high_volume_throttle

    def set_max_attempts(self, attempts: int) -> FeeEstimateQuery:
        """Set retry attempt limit."""
        if not isinstance(attempts, int):
            raise TypeError("attempts must be an integer")

        if attempts < 1:
            raise ValueError("attempts must be >= 1")

        self._max_attempts = attempts
        return self

    def set_max_backoff(self, seconds: float) -> FeeEstimateQuery:
        """Set maximum exponential backoff delay."""
        if not isinstance(seconds, (int | float)):
            raise TypeError("seconds must be a number")

        if seconds <= 0:
            raise ValueError("seconds must be > 0")

        self._max_backoff = float(seconds)
        return self

    def execute(self, client) -> FeeEstimateResponse:
        """
        Execute the fee estimation query.

        Returns:
            FeeEstimateResponse

        Raises:
            ValueError: if no transaction is set or request is invalid (HTTP 400)
        """
        if self._transaction is None:
            raise ValueError("Transaction must be set")

        mode = self._mode or FeeEstimateMode.INTRINSIC
        url = self._build_url(client, mode)

        if "localhost:38081" in url or "127.0.0.1:38081" in url:
            url = url.replace(":38081", ":8084")

        self._ensure_frozen(self._transaction, client)

        if self._is_chunked():
            return self._execute_chunked(client, url, mode)

        return self._execute_single(url, mode)

    def _build_url(self, client: Client, mode: FeeEstimateMode) -> str:
        base = f"{client.network.get_mirror_rest_url()}/network/fees"

        query = {
            "mode": mode.name,
            "high_volume_throttle": self._high_volume_throttle,
        }

        return f"{base}?{urlencode(query)}"

    def _ensure_frozen(self, tx: Transaction, client) -> None:
        """Ensure the transaction is frozen before serialization."""
        if not tx._transaction_body_bytes:
            tx.freeze_with(client) if hasattr(tx, "freeze_with") else tx.freeze()

    def _post(self, url: str, payload: bytes) -> dict:
        """POST with retry for transient failures."""
        for attempt in range(self._max_attempts):
            try:
                resp = requests.post(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/protobuf"},
                    timeout=10,
                )

                if resp.status_code == 200:
                    return resp.json()

                retryable_statuses = {408, 429, 500, 502, 503, 504}
                if resp.status_code not in retryable_statuses or attempt == self._max_attempts - 1:
                    raise RuntimeError(
                        f"Failed to fetch fee estimate. HTTP status: {resp.status_code} body: {resp.text}"
                    )

                error_msg = f"HTTP status: {resp.status_code}"

            except (requests.Timeout, requests.ConnectionError) as exc:  # noqa: PERF203
                if attempt == self._max_attempts - 1:
                    raise

                error_msg = str(exc)

            delay = min(0.5 * (2**attempt), self._max_backoff)
            logger.debug("Retrying after error: %s (%.2fs)", error_msg, delay)
            time.sleep(delay)

        raise RuntimeError("Unreachable")

    def _execute_single(self, url: str, mode: FeeEstimateMode) -> FeeEstimateResponse:
        data = self._post(url, self._transaction._to_proto().SerializeToString())
        return self._to_response(data, mode)

    def _execute_chunked(self, client, url: str, mode: FeeEstimateMode) -> FeeEstimateResponse:
        """
        Aggregate fees across all chunks into a single response.
        """

        # Save original state to restore later
        original_id = self._transaction.transaction_id
        original_index = getattr(self._transaction, "_current_chunk_index", 0)
        original_bodies = dict(self._transaction._transaction_body_bytes)
        original_signatures = dict(self._transaction._signature_map)

        total_node_base = 0
        total_service_base = 0
        total_network_subtotal = 0
        total_combined = 0
        node_extras: list[FeeExtra] = []
        service_extras: list[FeeExtra] = []

        final_multiplier = 0
        final_hvm = 0

        try:
            for i, chunk_tx_id in enumerate(self._transaction._transaction_ids):
                self._transaction._current_chunk_index = i
                self._transaction.transaction_id = chunk_tx_id

                self._transaction._transaction_body_bytes.clear()

                self._transaction.freeze_with(client)

                tx_bytes = self._transaction._to_proto().SerializeToString()
                data = self._post(url, tx_bytes)
                response = self._to_response(data, mode)

                if response.node_fee:
                    total_node_base += response.node_fee.base
                    node_extras.extend(response.node_fee.extras)
                if response.service_fee:
                    total_service_base += response.service_fee.base
                    service_extras.extend(response.service_fee.extras)
                if response.network_fee:
                    total_network_subtotal += response.network_fee.subtotal
                    final_multiplier = response.network_fee.multiplier
                total_combined += response.total

                final_hvm = response.high_volume_multiplier

        finally:
            self._transaction.transaction_id = original_id
            self._transaction._current_chunk_index = original_index
            self._transaction._transaction_body_bytes.clear()
            self._transaction._transaction_body_bytes.update(original_bodies)
            self._transaction._signature_map.clear()
            self._transaction._signature_map.update(original_signatures)

        return FeeEstimateResponse(
            mode=mode,
            node_fee=FeeEstimate(base=total_node_base, extras=node_extras),
            service_fee=FeeEstimate(base=total_service_base, extras=service_extras),
            network_fee=NetworkFee(multiplier=final_multiplier, subtotal=total_network_subtotal),
            total=total_combined,
            high_volume_multiplier=final_hvm,
        )

    def _to_response(self, data: dict, mode: FeeEstimateMode) -> FeeEstimateResponse:

        node_data = data.get("node", {})
        service_data = data.get("service", {})
        network_data = data.get("network", {})

        node_fee = FeeEstimate(base=node_data.get("base", 0), extras=self._parse_extras(node_data.get("extras")))

        service_fee = FeeEstimate(
            base=service_data.get("base", 0), extras=self._parse_extras(service_data.get("extras"))
        )

        network_fee = NetworkFee(multiplier=network_data.get("multiplier", 1), subtotal=network_data.get("subtotal", 0))

        total = data.get("total", 0)
        high_volume_multiplier = data.get("high_volume_multiplier", 0)

        return FeeEstimateResponse(
            mode=mode,
            node_fee=node_fee,
            service_fee=service_fee,
            network_fee=network_fee,
            total=total,
            high_volume_multiplier=high_volume_multiplier,
        )

    def _parse_extras(self, extra_list: list[dict]) -> list[FeeExtra]:
        if not extra_list:
            return []
        return [
            FeeExtra(
                name=item.get("name", None),
                included=item.get("included", 0),
                count=item.get("count", 0),
                charged=item.get("charged", 0),
                fee_per_unit=item.get("fee_per_unit", 0),
                subtotal=item.get("subtotal", 0),
            )
            for item in extra_list
        ]

    def _is_chunked(self) -> bool:
        return self._transaction.get_required_chunks() > 1
