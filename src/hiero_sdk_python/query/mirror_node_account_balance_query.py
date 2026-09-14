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
from urllib.parse import quote

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_mirror_node_balance import (
    MirrorNodeAccountBalance,
)
from hiero_sdk_python.client.client import Client


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

    def __init__(self) -> None:
        self._account_id: AccountId | None = None
        self._max_attempts = 10
        self._max_backoff = 8.0

    def get_account_id(self) -> AccountId | None:
        """
        Return the account ID.

        Returns:
            The account ID, or None if it has not been set.
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

        self._account_id = account_id
        return self

    def get_max_attempts(self) -> int:
        """
        Return the maximum number of HTTP attempts.

        Returns:
            Maximum number of attempts.
        """
        return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> MirrorNodeAccountBalanceQuery:
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

        self._max_attempts = max_attempts
        return self

    def get_max_backoff(self) -> float:
        """
        Return the maximum retry backoff in seconds.

        Returns:
            Maximum backoff duration in seconds.
        """
        return self._max_backoff

    def set_max_backoff(self, max_backoff: float) -> MirrorNodeAccountBalanceQuery:
        """
        Set the maximum retry backoff in seconds.

        Args:
            max_backoff: Maximum backoff duration in seconds.

        Returns:
            This query instance.

        Raises:
            ValueError: If max_backoff is less than 0.5 seconds.
        """
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
            raise ValueError("INVALID_ACCOUNT_ID")

        return balance

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
        if self._account_id is None:
            raise ValueError("account_id must be set before executing MirrorNodeAccountBalanceQuery")

        mirror_rest_url = client.network.get_mirror_rest_url()

        account_param = self._to_account_id_param(self._account_id)

        return f"{mirror_rest_url}/api/v1/balances?account.id={quote(account_param, safe='')}"

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
        evm_address = getattr(account_id, "evm_address", None)

        if evm_address is not None:
            if isinstance(evm_address, bytes):
                return "0x" + evm_address.hex()

            return "0x" + str(evm_address)

        # Public key alias
        alias_key = getattr(account_id, "alias_key", None)

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
