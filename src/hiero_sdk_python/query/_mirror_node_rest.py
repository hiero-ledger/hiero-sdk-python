"""
Private helpers shared by the mirror node REST queries.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import Collection
from http import HTTPStatus
from typing import Any

import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import MirrorNodeError


LOGGER = logging.getLogger(__name__)

# Upper bound for a single HTTP attempt, in seconds.
DEFAULT_PER_REQUEST_TIMEOUT = 30.0

# Local mirror nodes (solo, local-node) serve the web3 endpoints such as
# POST /contracts/call on a separate port from the rest of the REST API.
_LOCAL_REST_PORT = ":38081"
_LOCAL_WEB3_PORT = ":8545"


def to_web3_rest_url(rest_url: str) -> str:
    """
    Return the base URL that serves the mirror node web3 endpoints.

    Public mirror nodes serve them on the same host as the rest of the REST
    API. A local mirror node on localhost:38081 serves them on port 8545.
    """
    if f"localhost{_LOCAL_REST_PORT}" in rest_url or f"127.0.0.1{_LOCAL_REST_PORT}" in rest_url:
        return rest_url.replace(_LOCAL_REST_PORT, _LOCAL_WEB3_PORT)

    return rest_url


def send_with_retry(
    method: str,
    url: str,
    *,
    timeout: float,
    max_attempts: int,
    max_backoff: float,
    retryable_statuses: Collection[int],
    json_body: dict[str, Any] | None = None,
    description: str = "mirror node request",
) -> requests.Response:
    """
    Send an HTTP request to the mirror node, retrying transient failures.

    Timeouts, connection errors and any status in ``retryable_statuses`` are
    retried with capped exponential backoff. ``timeout`` is the total deadline
    for the whole call, including retries and backoff; each attempt is
    additionally bounded by ``DEFAULT_PER_REQUEST_TIMEOUT``.

    Args:
        method: The HTTP method, for example ``"GET"`` or ``"POST"``.
        url: The full request URL.
        timeout: Total deadline in seconds.
        max_attempts: Maximum number of attempts, including the first one.
        max_backoff: Maximum delay between attempts in seconds.
        retryable_statuses: HTTP statuses that are retried.
        json_body: Optional body, sent as ``application/json``.
        description: What is being fetched, used in log and error messages.

    Returns:
        The first response whose status is not retryable, or the last response
        if every attempt returned a retryable status. The caller decides what
        the status means.

    Raises:
        RuntimeError: If the total deadline is exceeded, or the last attempt
            failed with a timeout or connection error.
    """
    headers = {"Accept": "application/json"}
    data = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body)

    last_exception: Exception | None = None
    last_response: requests.Response | None = None
    deadline = time.monotonic() + timeout

    for attempt in range(1, max_attempts + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                f"{description} failed after {attempt - 1} attempts: total timeout of {timeout}s exceeded"
            ) from last_exception

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=data,
                timeout=min(DEFAULT_PER_REQUEST_TIMEOUT, remaining),
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exception = exc
            last_response = None
        else:
            if response.status_code not in retryable_statuses:
                return response

            last_exception = RuntimeError(f"HTTP {response.status_code}")
            last_response = response

        if attempt < max_attempts:
            _delay_before_retry(
                attempt,
                max_attempts,
                max_backoff,
                last_exception,
                deadline - time.monotonic(),
                description,
            )

    if last_response is not None:
        return last_response

    raise RuntimeError(f"{description} failed after {max_attempts} attempts") from last_exception


def _delay_before_retry(
    attempt: int,
    max_attempts: int,
    max_backoff: float,
    error: Exception | None,
    cap: float,
    description: str,
) -> None:
    """Log a retry and sleep using capped exponential backoff, never beyond the remaining budget."""
    delay = max(0.0, min(0.5 * (2**attempt), max_backoff, cap))
    LOGGER.warning(
        "Error during %s (attempt %d/%d). Retrying in %.1fs: %s",
        description,
        attempt,
        max_attempts,
        delay,
        error,
    )
    time.sleep(delay)


def mirror_node_error_from_response(response: requests.Response) -> MirrorNodeError:
    """
    Build a MirrorNodeError from an error response.

    The mirror node reports the reason in ``_status.messages[]``, where each
    entry has a ``message`` and optionally a ``detail`` and ``data``. When the
    body has no messages, the HTTP reason phrase is used instead.
    """
    messages: list[str] = []
    data: list[str] = []

    try:
        body = response.json()
    except ValueError:
        body = None

    status = body.get("_status") if isinstance(body, dict) else None
    entries = status.get("messages") if isinstance(status, dict) else None

    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            text = entry.get("message")
            detail = entry.get("detail")
            parts = [str(part) for part in (text, detail) if part]
            if parts:
                messages.append(": ".join(parts))

            if entry.get("data"):
                data.append(str(entry["data"]))

    if not messages:
        try:
            messages.append(HTTPStatus(response.status_code).phrase)
        except ValueError:
            pass

    return MirrorNodeError(response.status_code, messages, data)


def to_account_id_param(account_id: AccountId) -> str:
    """
    Convert an AccountId to the format expected by the mirror node.

    Plain account IDs are sent as shard.realm.num.

    EVM addresses are sent as 0x-prefixed hexadecimal.

    Public-key aliases are sent as unpadded Base32 encoded protobuf
    key bytes.
    """
    # EVM address
    evm_address = account_id.evm_address

    if evm_address is not None:
        if isinstance(evm_address, bytes):
            return "0x" + evm_address.hex()

        return "0x" + str(evm_address)

    # Public key alias
    alias_key = account_id.alias_key

    if alias_key is not None:
        # The exact conversion here depends on the Python SDK's
        # PublicKey/Key protobuf implementation.
        #
        # This corresponds to:
        #
        # BaseEncoding.base32()
        #     .omitPadding()
        #     .encode(accountId.aliasKey.toProtoKey().toByteArray());

        protobuf_key = alias_key.to_proto_key()
        key_bytes = protobuf_key.SerializeToString()

        return base64.b32encode(key_bytes).decode("ascii").rstrip("=")

    # Standard shard.realm.num account ID
    return str(account_id)
