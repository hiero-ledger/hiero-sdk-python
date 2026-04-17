"""Query module for retrieving fee estimates.

Defines the FeeEstimateQuery used to request fee estimation data
from the network or fee service.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, TYPE_CHECKING

import requests

from hiero_sdk_python.fees.fee_estimate import FeeEstimate
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.fees.fee_estimate_response import FeeEstimateResponse
from hiero_sdk_python.fees.network_fee import NetworkFee

if TYPE_CHECKING:
    from hiero_sdk_python.transaction.transaction import Transaction

logger = logging.getLogger(__name__)

class FeeEstimateQuery:
    """
    Builds and executes a request to retrieve fee estimates for a transaction.

    This class is responsible for preparing a transaction, selecting a fee
    estimation mode, and querying the network (via the configured mirror
    network endpoint) to obtain estimated node, service, and network fees.

    It handles transaction freezing, serialization, retry logic with
    backoff, and response parsing into a structured `FeeEstimateResponse`.

    Attributes:
        _mode: The fee estimation mode used for the query (e.g., STATE or INTRINSIC).
        _transaction: The transaction being evaluated for fee estimation.
        _max_attempts: Maximum number of retry attempts for network requests.
        _max_backoff: Maximum backoff delay (in seconds) between retries.
    """

    def __init__(self):
        """
        Initializes a new FeeEstimateQuery instance.

        Sets default configuration values for fee estimation, including the
        default retry policy and optional transaction/mode settings.

        Attributes:
            _mode: The fee estimation mode to use (STATE or INTRINSIC). Defaults to None.
            _transaction: The transaction being evaluated for fee estimation. Defaults to None.
            _max_attempts: Maximum number of retry attempts for network requests. Defaults to 10.
            _max_backoff: Maximum backoff delay (in seconds) between retries.
            Defaults to 0 (no delay).
        """
        self._mode: FeeEstimateMode | None = None
        self._transaction: Optional[Transaction] = None
        self._max_attempts = 10
        self._max_backoff = 0

    def set_mode(self, mode: FeeEstimateMode) -> "FeeEstimateQuery":
        """Set the fee estimation mode for the query.

        Args:
            mode: The fee estimation mode to use (e.g., STATE or INTRINSIC).

        Returns:
            The current FeeEstimateQuery instance for method chaining.
        """
        self._mode = mode
        return self

    def get_mode(self) -> FeeEstimateMode | None:
        """Get the currently set fee estimation mode.

        Returns:
            The fee estimation mode if set, otherwise None.
        """
        return self._mode

    def set_transaction(self, transaction: Transaction) -> FeeEstimateQuery:
        """Attach a transaction to this fee estimation query.

        The provided transaction will be used to calculate estimated fees.

        Args:
            transaction: The transaction to evaluate.

        Returns:
            The current FeeEstimateQuery instance for method chaining.
        """
        # if hasattr(transaction, "freeze") and not transaction.is_frozen:
        # transaction.freeze()

        # if hasattr(transaction, "freeze") and not getattr(transaction, "is_frozen", False):
        # transaction.freeze()

        self._transaction = transaction
        return self

    def get_transaction(self) -> Transaction | None:
        """Get the transaction associated with this query.

        Returns:
            The transaction if set, otherwise None.
        """

        return self._transaction

    def _backoff(self, attempt: int):
        """Sleep using exponential backoff."""
        delay = min(0.5 * (2**attempt), self._max_backoff)
        time.sleep(delay)

    def _ensure_frozen(self, transaction, client):
        """Ensure transaction is frozen before execution."""

        # pylint: disable=protected-access
        try:
            transaction._require_frozen()
        except (AttributeError, ValueError, RuntimeError):
            # fallback: fully prepare transaction before serialization
            if hasattr(transaction, "freeze_with"):
                transaction.freeze_with(client)
            else:
                transaction.freeze()

    def set_max_attempts(self, attempts: int) -> FeeEstimateQuery:
        """Set maximum retry attempts."""
        self._max_attempts = attempts
        return self

    def get_max_attempts(self) -> int:
        """Get maximum retry attempts."""
        return self._max_attempts

    def set_max_backoff(self, backoff: int) -> FeeEstimateQuery:
        """Set maximum backoff duration."""
        self._max_backoff = backoff
        return self

    def get_max_backoff(self) -> int:
        """Get maximum backoff duration."""
        return self._max_backoff

    def _serialize_transaction(self, transaction, client) -> bytes:
        try:
            return transaction.to_bytes()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("to_bytes() failed, attempting freeze fallback: %s", exc)

        try:
            transaction.freeze_with(client)
            return transaction.to_bytes()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("freeze_with() failed, using protobuf fallback: %s", exc)

        try:
            body = transaction.build_transaction_body()
            return body.SerializeToString() if body else b""
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("All serialization methods failed: %s", exc)
            return b""

    def _post_with_retry(self, url: str, data: bytes, max_retries: int = 2):
        """POST request with retry logic for transient failures."""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/protobuf"},
                    timeout=10,
                )

                if response.status_code == 400:
                    raise ValueError("Invalid argument")

                return response

            except Exception as exc:  # pylint: disable=broad-exception-caught
                if attempt == max_retries - 1:
                    raise

                msg = str(exc)

                if "UNAVAILABLE" in msg or "DEADLINE_EXCEEDED" in msg:
                    self._backoff(attempt)
                    continue

                raise

        return None

    def execute(self, client) -> FeeEstimateResponse:
        """Execute fee estimation query against the network."""
        if self._transaction is None:
            raise ValueError("Transaction must be set")

        mode = self._mode or FeeEstimateMode.STATE
        url = f"{client.mirror_network}/api/v1/network/fees?mode={mode.value}"

        transaction_bytes = self._serialize_transaction(self._transaction, client)

        response = self._post_with_retry(url, transaction_bytes)

        data = response.json()

        node_total = data.get("node", {}).get("subtotal", 0)
        service_total = data.get("service", {}).get("subtotal", 0)
        network_multiplier = data.get("network", {}).get("multiplier", 0)
        notes = data.get("notes", [])

        network_total = node_total * network_multiplier
        total = node_total + service_total + network_total

        return FeeEstimateResponse(
            mode=mode,
            node_fee=FeeEstimate(base=node_total, extras=[]),
            service_fee=FeeEstimate(base=service_total, extras=[]),
            network_fee=NetworkFee(
                multiplier=network_multiplier,
                subtotal=network_total,
            ),
            notes=notes,
            total=total,
        )

    def _parse_response(self, data):
        """Parse raw fee response into structured FeeEstimateResponse."""
        node_fee = FeeEstimate(base=data["node"]["subtotal"], extras=[])

        service_fee = FeeEstimate(base=data["service"]["subtotal"], extras=[])

        network_fee = NetworkFee(
            multiplier=data["network"]["multiplier"], subtotal=0  # computed later
        )

        return FeeEstimateResponse(
            mode=FeeEstimateMode(data["mode"]),
            network_fee=network_fee,
            node_fee=node_fee,
            service_fee=service_fee,
            notes=data.get("notes", []),
            total=0,  # computed later
        )
