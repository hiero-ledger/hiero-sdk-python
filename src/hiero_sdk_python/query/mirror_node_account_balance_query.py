"""
Mirror Node Account Balance Query.

Gets the HBAR balance of an account from the mirror node REST API.

This is the replacement for CryptoGetAccountBalanceQuery, which relies on
the consensus node CryptoService/cryptoGetBalance endpoint.

Only the HBAR balance is returned. Token balances are not covered by this
query.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_mirror_node_balance import (
    MirrorNodeAccountBalance,
)
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError


LOGGER = logging.getLogger(__name__)


class MirrorNodeAccountBalanceQuery:
    """
    Get the HBAR balance of an account from the mirror node REST API.

    The account may be identified by:
    - shard.realm.num
    - an EVM address
    - a public key alias

    Only the HBAR balance is returned.
    """

    def __init__(self, account_id: AccountId) -> None:
        if account_id is None:
            raise ValueError("account_id must not be None")

        self._account_id = account_id
        self._max_attempts = 10
        self._max_backoff = 8.0

    @property
    def get_account_id(self) -> AccountId:
        """
        Return the account ID.

        Returns:
            The account ID.
        """
        return self._account_id

    def set_account_id(self, account_id: AccountId) -> MirrorNodeAccountBalanceQuery:
        """
        Set the account ID for which the balance is requested.

        Args:
            account_id: The account ID.

        Returns:
            This query instance.
        """
        if account_id is None:
            raise ValueError("account_id must not be None")

        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance")

        self._account_id = account_id
        return self

    @property
    def max_attempts(self) -> int:
        """
        Return the maximum number of HTTP attempts.

        Returns:
            Maximum number of attempts.
        """
        return self._max_attempts

    def set_max_attempts(
        self,
        max_attempts: int,
    ) -> MirrorNodeAccountBalanceQuery:
        """
        Set the maximum number of HTTP attempts.

        Args:
            max_attempts: Maximum number of attempts.

        Returns:
            This query instance.

        Raises:
            ValueError: If max_attempts is not greater than zero.
        """
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")

        if not isinstance(max_attempts, int):
            raise TypeError("max_attempts must be an integer")

        self._max_attempts = max_attempts
        return self

    @property
    def max_backoff(self) -> float:
        """
        Return the maximum retry backoff in seconds.

        Returns:
            Maximum backoff duration in seconds.
        """
        return self._max_backoff

    def set_max_backoff(
        self,
        max_backoff: float,
    ) -> MirrorNodeAccountBalanceQuery:
        """
        Set the maximum retry backoff in seconds.

        Args:
            max_backoff: Maximum backoff duration in seconds.

        Returns:
            This query instance.

        Raises:
            TypeError: If max_backoff is not a number.
            ValueError: If max_backoff is less than 0.5 seconds.
        """
        if not isinstance(max_backoff, (int, float)):
            raise TypeError("max_backoff must be a number")

        if max_backoff < 0.5:
            raise ValueError("max_backoff must be at least 0.5 seconds")

        self._max_backoff = max_backoff
        return self

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        """
        Determine whether an HTTP status code should be retried.
        """
        return status_code == 408 or status_code == 429 or 500 <= status_code < 600

    def execute(
        self,
        client: Client,
        timeout: float | None = None,
    ) -> MirrorNodeAccountBalance:
        """
        Execute the query synchronously.

        Args:
            client: The client used to determine the mirror node URL.
            timeout: Maximum duration for each HTTP request in seconds.

        Returns:
            The retrieved MirrorNodeAccountBalance.

        Raises:
            ValueError: If the query is not properly configured.
            PrecheckError: If the account ID is invalid.
            RuntimeError: If the mirror node request fails.
        """
        if client is None:
            raise ValueError("client must not be None")

        if timeout is None:
            timeout = getattr(client, "request_timeout", 30.0)

        url = self._build_url(client)

        body = self._fetch_body(url, timeout)

        try:
            root = body
            balance = MirrorNodeAccountBalance.from_json(root)
        except (ValueError, TypeError) as exc:
            raise ValueError("Mirror Node returned a malformed JSON response") from exc

        if balance is None:
            # The mirror node returns HTTP 200 with an empty balances array
            # when it does not know the requested account.
            raise PrecheckError("INVALID_ACCOUNT_ID")

        return balance

    def _request(
        self,
        url: str,
        timeout: float,
    ) -> tuple[Any | None, Exception | None]:
        """
        Make an HTTP GET request to the mirror node.
        Args:
            url: Mirror node REST endpoint.
            timeout: HTTP request timeout in seconds.

        Returns:
            A tuple containing the response and an optional exception.
        """
        try:
            request = Request(
                url,
                method="GET",
                headers={
                    "Accept": "application/json",
                },
            )

            response = urlopen(request, timeout=timeout)  # nosec B310

            class Response:
                def __init__(self, response):
                    self.status_code = response.status
                    self._response = response

                def json(self):
                    import json

                    return json.loads(self._response.read().decode("utf-8"))

            return Response(response), None

        except HTTPError as exc:

            class ErrorResponse:
                def __init__(self, status_code):
                    self.status_code = status_code

            return ErrorResponse(exc.code), None

        except (URLError, TimeoutError, OSError) as exc:
            return None, exc

    def _fetch_body(
        self,
        url: str,
        timeout: float,
    ) -> dict[str, Any]:
        """
        Fetch and decode the mirror node response with retries.
        """
        last_exception: Exception | None = None

        for attempt in range(1, self._max_attempts + 1):
            response, request_exception = self._request(url, timeout)

            if request_exception is not None:
                last_exception = request_exception

                if attempt >= self._max_attempts:
                    raise RuntimeError(
                        f"Failed to fetch account balance after {attempt} attempts"
                    ) from request_exception

                self._warn_and_delay(attempt, request_exception)
                continue

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise ValueError("Mirror Node returned a malformed JSON response") from exc

            if not self._should_retry_status(response.status_code) or attempt >= self._max_attempts:
                raise RuntimeError(f"Mirror Node error: HTTP {response.status_code}")

            last_exception = RuntimeError(f"HTTP {response.status_code}")

            self._warn_and_delay(attempt, last_exception)

        raise RuntimeError(f"Failed to fetch account balance after {self._max_attempts} attempts") from last_exception

    def _build_url(self, client: Client) -> str:
        """
        Build the mirror node balance endpoint URL.
        """
        mirror_rest_url = client.network.get_mirror_rest_url().rstrip("/")

        account_param = self._to_account_id_param(self._account_id)

        return f"{mirror_rest_url}/balances?account.id={quote(account_param, safe='')}"

    @staticmethod
    def _to_account_id_param(account_id: AccountId) -> str:
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
            #     .encode(accountId.aliasKey.toProtobufKey().toByteArray());

            protobuf_key = alias_key.to_protobuf_key()
            key_bytes = protobuf_key.SerializeToString()

            return base64.b32encode(key_bytes).decode("ascii").rstrip("=")

        # Standard shard.realm.num account ID
        return str(account_id)

    def _warn_and_delay(
        self,
        attempt: int,
        error: Exception,
    ) -> None:
        """
        Log a retry and wait using exponential backoff.
        """
        delay_ms = min(
            500 * (2**attempt),
            self._max_backoff * 1000,
        )

        LOGGER.warning(
            "Error fetching account balance during attempt #%s. Waiting %s ms before next attempt: %s",
            attempt,
            int(delay_ms),
            str(error),
        )

        time.sleep(delay_ms / 1000)

    def __str__(self) -> str:
        return f"MirrorNodeAccountBalanceQuery(account_id={self._account_id})"
