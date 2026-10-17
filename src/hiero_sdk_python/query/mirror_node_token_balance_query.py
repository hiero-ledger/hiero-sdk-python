from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import quote

import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.mirror_node_token_balance import MirrorNodeTokenBalance
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query._mirror_node_rest import to_account_id_param
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId


logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}
_DEFAULT_PER_REQUEST_TIMEOUT = 30


class MirrorNodeTokenBalanceQuery:
    """
    Queries the balance of a specific token held by an account using the Mirror Node REST API.

    This query retrieves token balance information from the following endpoint:
    GET /api/v1/accounts/{id}/tokens?token.id={token_id}&limit=1

    The account may be identified by a shard.realm.num id, an EVM address or a public-key alias.

    The ``timeout`` passed to ``execute`` is the total deadline for the whole call, including
    retries and backoff; each individual HTTP attempt is additionally bounded at 30 seconds.
    The per-attempt bound is applied by ``requests`` to connecting and to each read, so a
    response that keeps trickling bytes can run slightly past it.

    An HTTP 404 (unknown account) raises ``PrecheckError(ResponseCode.INVALID_ACCOUNT_ID)``. An empty
    ``tokens`` array (the account exists but has no relationship with the token) yields a balance of 0,
    decimals of 0 and ``associated=False``.

    This API may change once hiero-ledger/sdk-collaboration-hub#281 is finalised.

    Results are not read-after-write consistent: the mirror node lags consensus by a few seconds, so a
    balance queried immediately after a transaction may not yet reflect it.

    Attributes:
        account_id (AccountId): The account whose token balance is requested.
        token_id (TokenId): The token whose balance is requested.
    """

    def __init__(self, account_id: AccountId | None = None, token_id: TokenId | None = None):
        self._account_id: AccountId | None = None
        if account_id is not None:
            self.set_account_id(account_id)

        self._token_id: TokenId | None = None
        if token_id is not None:
            self.set_token_id(token_id)

        self._max_attempts: int = 10
        self._max_backoff: float = 8.0  # 8 seconds

    @property
    def account_id(self) -> AccountId | None:
        """Return the account ID."""
        return self._account_id

    def set_account_id(self, account_id: AccountId) -> MirrorNodeTokenBalanceQuery:
        """
        Set the account whose token balance will be queried.

        Args:
            account_id: The account ID to query.

        Returns:
            This query instance for method chaining.

        Raises:
            TypeError: If account_id is not an AccountId.
        """
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be of type AccountId")

        self._account_id = account_id
        return self

    @property
    def token_id(self) -> TokenId | None:
        """Return the token ID."""
        return self._token_id

    def set_token_id(self, token_id: TokenId) -> MirrorNodeTokenBalanceQuery:
        """
        Set the token whose balance will be queried.

        Args:
            token_id: The token ID to query.

        Returns:
            This query instance for method chaining.

        Raises:
            TypeError: If token_id is not a TokenId.
        """
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be of type TokenId")

        self._token_id = token_id
        return self

    @property
    def max_attempts(self) -> int:
        """Return the maximum number of request attempts."""
        return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> MirrorNodeTokenBalanceQuery:
        """
        Set the maximum number of HTTP request attempts.

        The initial request counts as the first attempt.

        Args:
            max_attempts: Maximum number of attempts. Must be at least 1.

        Returns:
            This query instance for method chaining.

        Raises:
            TypeError: If max_attempts is not an integer.
            ValueError: If max_attempts is less than 1.
        """
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise TypeError("max_attempts must be an integer")

        if max_attempts <= 0:
            raise ValueError("max_attempts must be at least 1")

        self._max_attempts = max_attempts
        return self

    @property
    def max_backoff(self) -> float:
        """Return the maximum retry delay in seconds."""
        return self._max_backoff

    def set_max_backoff(self, max_backoff: int | float) -> MirrorNodeTokenBalanceQuery:
        """
        Set the maximum delay between retry attempts.

        Args:
            max_backoff: Maximum retry delay in seconds. Must be at least 0.5.

        Returns:
            This query instance for method chaining.

        Raises:
            TypeError: If max_backoff is not a number.
            ValueError: If max_backoff is less than 0.5 seconds.
        """
        if isinstance(max_backoff, bool) or not isinstance(max_backoff, (int, float)):
            raise TypeError("max_backoff must be a number")

        if max_backoff < 0.5:
            raise ValueError("max_backoff must be at least 0.5 seconds")

        self._max_backoff = max_backoff
        return self

    def execute(self, client: Client, timeout: int | float | None = None) -> MirrorNodeTokenBalance:
        """
        Execute the query and return the account's token balance.

        Args:
            client: The client used to access the Mirror Node.
            timeout: Total deadline in seconds for the whole call, including retries and
                backoff. Each HTTP attempt is bounded by min(30, remaining time).
                Defaults to the client's configured request timeout.

        Returns:
            The token balance reported by the Mirror Node.

        Raises:
            PrecheckError: With ResponseCode.INVALID_ACCOUNT_ID if the Mirror Node returns HTTP 404.
            RuntimeError: If the Mirror Node returns a non-retryable error status, or retries
                or the total deadline are exhausted.
            ValueError: If required parameters are missing, timeout is not positive, or the
                response is not valid JSON or contains malformed data.
            TypeError: If an argument has an invalid type.
            requests.RequestException: For transport failures other than timeouts and
                connection errors (for example a truncated response), which are not retried.
        """

        if client is None:
            raise ValueError("client must not be None")
        if not isinstance(client, Client):
            raise TypeError("client must be of type Client")

        if timeout is None:
            timeout = client._request_timeout
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a number")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        if self.account_id is None:
            raise ValueError("account_id must be set before executing MirrorNodeTokenBalanceQuery")

        if self.token_id is None:
            raise ValueError("token_id must be set before executing MirrorNodeTokenBalanceQuery")

        url = self._build_url(client)
        response = self._fetch_token_balance(url, timeout)

        try:
            return MirrorNodeTokenBalance._from_json(response, self.token_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Mirror Node returned a malformed JSON response") from e

    def _build_url(self, client: Client) -> str:
        """Build the Mirror Node token balance endpoint URL."""
        mirror_rest_url = client.network.get_mirror_rest_url().rstrip("/")
        account_param = quote(self._to_account_id_param(self._account_id), safe="")
        token_param = quote(str(self._token_id), safe="")

        return f"{mirror_rest_url}/accounts/{account_param}/tokens?token.id={token_param}&limit=1"

    def _fetch_token_balance(self, url: str, timeout: float) -> dict[str, Any]:
        """
        Fetch the token balance JSON with retries and exponential backoff.

        The timeout is the total deadline for the whole operation, including retries and
        backoff sleeps. Each HTTP request is bounded by min(30, remaining time).

        Raises:
            PrecheckError: With INVALID_ACCOUNT_ID on HTTP 404 (not retried).
            RuntimeError: On a non-retryable HTTP status, or when attempts or the deadline are exhausted.
            ValueError: If a 200 response body is not valid JSON.
        """
        last_exception: Exception | None = None
        deadline = time.monotonic() + timeout

        for attempt in range(1, self._max_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(
                    f"Failed to fetch MirrorNodeTokenBalance after {attempt - 1} attempts: "
                    f"total timeout of {timeout}s exceeded"
                ) from last_exception

            try:
                attempt_timeout = min(_DEFAULT_PER_REQUEST_TIMEOUT, remaining)
                resp = requests.get(url, timeout=attempt_timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                last_exception = e
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError as e:
                        raise ValueError("Mirror Node returned a malformed JSON response") from e

                if resp.status_code == 404:
                    raise PrecheckError(ResponseCode.INVALID_ACCOUNT_ID)

                if resp.status_code not in _RETRYABLE_HTTP_STATUSES:
                    raise RuntimeError(f"Mirror Node error: HTTP {resp.status_code}")

                last_exception = RuntimeError(f"HTTP {resp.status_code}")

            if attempt < self._max_attempts:
                self._delay_for_attempt(attempt, last_exception, deadline - time.monotonic())

        raise RuntimeError(
            f"Failed to fetch MirrorNodeTokenBalance after {self._max_attempts} attempts"
        ) from last_exception

    @staticmethod
    def _to_account_id_param(account_id: AccountId) -> str:
        """Convert an account ID to its mirror node URL representation."""
        return to_account_id_param(account_id)

    def _delay_for_attempt(self, attempt: int, e: Exception | None, cap: float = float("inf")) -> None:
        """Log a retry and sleep using capped exponential backoff, never beyond the remaining budget."""
        delay = max(0.0, min(0.5 * (2**attempt), self._max_backoff, cap))
        logger.warning(
            "Error fetching MirrorNodeTokenBalance (attempt %d/%d). Retrying in %.1fs: %s",
            attempt,
            self._max_attempts,
            delay,
            e,
        )
        time.sleep(delay)
