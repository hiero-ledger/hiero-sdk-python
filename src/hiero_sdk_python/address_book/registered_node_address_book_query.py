"""Query for fetching the registered-node address book from the mirror node."""

from __future__ import annotations

import logging
import time
from urllib.parse import urlencode

import requests

from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.address_book.registered_node_address_book import (
    RegisteredNodeAddressBook,
)


logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 25
_RETRYABLE_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}


class RegisteredNodeAddressBookQuery:
    """Query to retrieve the registered-node address book from the mirror node REST API.

    The query hits ``GET /api/v1/network/registered-nodes`` and follows
    pagination links automatically.  Transient HTTP errors are retried with
    exponential back-off.
    """

    def __init__(self) -> None:
        self._max_registered_node_count: int | None = None
        self._registered_node_id: int | None = None
        self._limit: int = _DEFAULT_LIMIT
        self._max_attempts: int = 10
        self._max_backoff: float = 8.0

    # -- setters (fluent) ---------------------------------------------------

    def set_max_registered_node_count(self, count: int) -> RegisteredNodeAddressBookQuery:
        """Limit the total number of registered nodes returned.

        Args:
            count: Maximum number of nodes. Must be positive.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("count must be a positive integer")
        self._max_registered_node_count = count
        return self

    def set_registered_node_id(self, node_id: int) -> RegisteredNodeAddressBookQuery:
        """Filter the query to a single registered node.

        Args:
            node_id: The registered node identifier.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(node_id, int) or isinstance(node_id, bool) or node_id < 0:
            raise ValueError("node_id must be a non-negative integer")
        self._registered_node_id = node_id
        return self

    def set_limit(self, limit: int) -> RegisteredNodeAddressBookQuery:
        """Set the page size for each REST API request.

        Args:
            limit: Maximum nodes per page. Must be positive.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        self._limit = limit
        return self

    def set_max_attempts(self, attempts: int) -> RegisteredNodeAddressBookQuery:
        """Set the maximum number of retry attempts per page fetch.

        Args:
            attempts: Must be >= 1.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
            raise ValueError("attempts must be a positive integer")
        self._max_attempts = attempts
        return self

    def set_max_backoff(self, seconds: float) -> RegisteredNodeAddressBookQuery:
        """Set the maximum exponential back-off delay in seconds.

        Args:
            seconds: Must be > 0.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            raise ValueError("seconds must be a positive number")
        self._max_backoff = float(seconds)
        return self

    # -- execution ----------------------------------------------------------

    def execute(self, client) -> RegisteredNodeAddressBook:
        """Execute the query against the mirror node.

        Args:
            client: A :class:`Client` instance with a configured network.

        Returns:
            RegisteredNodeAddressBook containing the fetched nodes.

        Raises:
            RuntimeError: If a page fetch fails after all retry attempts.
        """
        if client is None:
            raise ValueError("client must not be None")

        base_url = self._build_base_url(client)
        path = self._build_initial_path()
        nodes: list[RegisteredNode] = []

        while path is not None:
            data = self._fetch_page(base_url + path)

            for entry in data.get("registered_nodes", []):
                nodes.append(RegisteredNode._from_dict(entry))
                if self._max_registered_node_count and len(nodes) >= self._max_registered_node_count:
                    return RegisteredNodeAddressBook(nodes=nodes)

            path = self._next_page_path(data)

        return RegisteredNodeAddressBook(nodes=nodes)

    # -- internals ----------------------------------------------------------

    def _build_base_url(self, client) -> str:
        """Derive the mirror-node base URL (without ``/api/v1``)."""
        rest_url = client.network.get_mirror_rest_url()  # e.g. http://localhost:38081/api/v1

        # For localhost / solo, use port 8084 for registered-node calls
        if "localhost:38081" in rest_url or "127.0.0.1:38081" in rest_url:
            rest_url = rest_url.replace(":38081", ":8084")

        # Strip /api/v1 suffix so we can append full paths from pagination links
        return rest_url.removesuffix("/api/v1")

    def _build_initial_path(self) -> str:
        params: dict[str, int] = {"limit": self._limit}
        if self._registered_node_id is not None:
            params["registerednode.id"] = self._registered_node_id
        return f"/api/v1/network/registered-nodes?{urlencode(params)}"

    def _fetch_page(self, url: str) -> dict:
        """GET a single page with retry and exponential back-off."""
        last_exc: Exception | None = None

        for attempt in range(self._max_attempts):
            try:
                resp = requests.get(url, timeout=30)

                if resp.status_code == 200:
                    return resp.json()

                if resp.status_code not in _RETRYABLE_HTTP_STATUSES or attempt == self._max_attempts - 1:
                    raise RuntimeError(f"Mirror node error: HTTP {resp.status_code} — {resp.text}")

                last_exc = RuntimeError(f"HTTP {resp.status_code}")

            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt == self._max_attempts - 1:
                    raise RuntimeError(f"Failed to fetch registered nodes after {self._max_attempts} attempts") from exc
                last_exc = exc

            delay = min(0.5 * (2**attempt), self._max_backoff)
            logger.warning(
                "Error fetching registered nodes (attempt %d/%d). Retrying in %.1fs: %s",
                attempt + 1,
                self._max_attempts,
                delay,
                last_exc,
            )
            time.sleep(delay)

        raise RuntimeError(f"Failed to fetch registered nodes after {self._max_attempts} attempts")

    @staticmethod
    def _next_page_path(data: dict) -> str | None:
        links = data.get("links")
        if links and isinstance(links, dict):
            return links.get("next")
        return None
