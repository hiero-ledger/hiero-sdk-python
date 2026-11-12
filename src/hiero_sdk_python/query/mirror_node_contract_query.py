"""
Base class for the mirror node contract queries.

The mirror node can simulate a contract call (``eth_call`` semantics) or
estimate the gas a call needs, through ``POST /api/v1/contracts/call``.
Both are free: there is no query payment and no consensus node round trip.

See MirrorNodeContractCallQuery and MirrorNodeContractEstimateGasQuery.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.query._mirror_node_rest import (
    mirror_node_error_from_response,
    send_with_retry,
    to_web3_rest_url,
)


# Transient server-side failures. 400 (bad input or a revert), 404, 415 and
# 429 are reported to the caller straight away.
_RETRYABLE_HTTP_STATUSES = frozenset({500, 502, 503, 504})

_EVM_ADDRESS_PATTERN = re.compile(r"[0-9a-fA-F]{40}")
# A 0x-prefixed hex string. "0x" alone is a valid call result (no return
# data), and gas estimates are hex quantities that may have an odd length.
_HEX_RESULT_PATTERN = re.compile(r"0x[0-9a-fA-F]*")


class MirrorNodeContractQuery(ABC):
    """
    Base class for contract queries answered by the mirror node.

    The query targets a contract given by ``set_contract_id`` or
    ``set_contract_evm_address`` (the EVM address wins when both are set).
    The call data is built with ``set_function`` or given raw with
    ``set_function_parameters``.

    These queries do not extend ``Query``: they use no gRPC, no payment and
    no node selection. The request goes to the client's mirror node REST URL.

    Results are not read-after-write consistent: the mirror node lags
    consensus by a few seconds. Until it imports a newly created contract,
    a query does not fail. It runs against an address with no code, so a
    call returns ``"0x"`` and a gas estimate is only the cost of a plain
    transfer, too low for the real call. Right after a
    ``ContractCreateTransaction`` or ``ContractExecuteTransaction``, wait
    until the mirror node returns the expected state before relying on a
    result.
    """

    _ESTIMATE: ClassVar[bool]

    def __init__(self, contract_id: ContractId | None = None) -> None:
        self._contract_id: ContractId | None = None
        self._contract_evm_address: str | None = None
        self._sender: AccountId | None = None
        self._sender_evm_address: str | None = None
        self._function_parameters: bytes | None = None
        self._value: int | None = None
        self._gas_limit: int | None = None
        self._gas_price: int | None = None
        self._block_number: int | None = None
        self._max_attempts: int = 10
        self._max_backoff: float = 8.0

        if contract_id is not None:
            self.set_contract_id(contract_id)

    # Contract

    @property
    def contract_id(self) -> ContractId | None:
        """Return the contract ID."""
        return self._contract_id

    def set_contract_id(self, contract_id: ContractId) -> Self:
        """
        Set the contract to call.

        The contract ID is converted to an EVM address when the query runs.
        An address set with ``set_contract_evm_address`` takes precedence.

        Args:
            contract_id: The contract ID.

        Returns:
            This query instance.

        Raises:
            TypeError: If contract_id is not a ContractId.
        """
        if not isinstance(contract_id, ContractId):
            raise TypeError("contract_id must be of type ContractId")

        self._contract_id = contract_id
        return self

    @property
    def contract_evm_address(self) -> str | None:
        """Return the contract EVM address as 40 hex characters without a ``0x`` prefix."""
        return self._contract_evm_address

    def set_contract_evm_address(self, contract_evm_address: str) -> Self:
        """
        Set the EVM address of the contract to call.

        Takes precedence over ``set_contract_id``.

        Args:
            contract_evm_address: The 20-byte address as hex, with or without a ``0x`` prefix.

        Returns:
            This query instance.

        Raises:
            TypeError: If contract_evm_address is not a string.
            ValueError: If contract_evm_address is not 40 hex characters.
        """
        self._contract_evm_address = _normalize_evm_address(contract_evm_address, "contract_evm_address")
        return self

    # Sender

    @property
    def sender(self) -> AccountId | None:
        """Return the sender account ID."""
        return self._sender

    def set_sender(self, sender: AccountId) -> Self:
        """
        Set the account the call is simulated from (``msg.sender``).

        Optional. The account ID is converted to an EVM address when the query
        runs. An address set with ``set_sender_evm_address`` takes precedence.

        A public-key alias without an account number has no EVM address the
        query can derive, so it is rejected; pass the sender's EVM address to
        ``set_sender_evm_address`` instead.

        Args:
            sender: The sender account ID.

        Returns:
            This query instance.

        Raises:
            TypeError: If sender is not an AccountId.
            ValueError: If sender is a public-key alias with no account number or EVM address.
        """
        if not isinstance(sender, AccountId):
            raise TypeError("sender must be of type AccountId")

        if sender.alias_key is not None and sender.evm_address is None and sender.num == 0:
            raise ValueError(
                "sender is a public-key alias with no account number, so its EVM address is unknown; "
                "use set_sender_evm_address() instead"
            )

        self._sender = sender
        return self

    @property
    def sender_evm_address(self) -> str | None:
        """Return the sender EVM address as 40 hex characters without a ``0x`` prefix."""
        return self._sender_evm_address

    def set_sender_evm_address(self, sender_evm_address: str) -> Self:
        """
        Set the EVM address the call is simulated from (``msg.sender``).

        Optional. Takes precedence over ``set_sender``.

        Args:
            sender_evm_address: The 20-byte address as hex, with or without a ``0x`` prefix.

        Returns:
            This query instance.

        Raises:
            TypeError: If sender_evm_address is not a string.
            ValueError: If sender_evm_address is not 40 hex characters.
        """
        self._sender_evm_address = _normalize_evm_address(sender_evm_address, "sender_evm_address")
        return self

    # Call data

    @property
    def function_parameters(self) -> bytes | None:
        """Return the raw call data."""
        return self._function_parameters

    def set_function(self, name: str, params: ContractFunctionParameters | None = None) -> Self:
        """
        Set the contract function to call and its arguments.

        The call data is the function selector followed by the ABI-encoded
        arguments, as in ``ContractCallQuery.set_function``.

        Args:
            name: The name of the function.
            params: The function arguments. If omitted, the function is called with no arguments.

        Returns:
            This query instance.

        Raises:
            TypeError: If name is not a string or params is not ContractFunctionParameters.
            ValueError: If name is empty.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        if not name:
            raise ValueError("name must not be empty")

        if params is None:
            params = ContractFunctionParameters()
        elif not isinstance(params, ContractFunctionParameters):
            raise TypeError("params must be of type ContractFunctionParameters")

        params.function_name = name

        self._function_parameters = params.to_bytes()
        return self

    def set_function_parameters(self, function_parameters: bytes | ContractFunctionParameters) -> Self:
        """
        Set the raw call data.

        Args:
            function_parameters: The call data as bytes, or ContractFunctionParameters
                to encode.

        Returns:
            This query instance.

        Raises:
            TypeError: If function_parameters is neither bytes nor ContractFunctionParameters.
        """
        if isinstance(function_parameters, ContractFunctionParameters):
            self._function_parameters = function_parameters.to_bytes()
        elif isinstance(function_parameters, (bytes, bytearray)):
            self._function_parameters = bytes(function_parameters)
        else:
            raise TypeError("function_parameters must be bytes or ContractFunctionParameters")

        return self

    # Call options

    @property
    def value(self) -> int | None:
        """Return the value sent with the call, in tinybars."""
        return self._value

    def set_value(self, value: int) -> Self:
        """
        Set the value sent with the call, in tinybars, for payable functions.

        Args:
            value: The value in tinybars.

        Returns:
            This query instance.

        Raises:
            TypeError: If value is not an integer.
            ValueError: If value is negative.
        """
        self._value = _validate_non_negative_int(value, "value")
        return self

    @property
    def gas_limit(self) -> int | None:
        """Return the gas limit."""
        return self._gas_limit

    def set_gas_limit(self, gas_limit: int) -> Self:
        """
        Set the gas limit for the call.

        Args:
            gas_limit: The gas limit.

        Returns:
            This query instance.

        Raises:
            TypeError: If gas_limit is not an integer.
            ValueError: If gas_limit is negative.
        """
        self._gas_limit = _validate_non_negative_int(gas_limit, "gas_limit")
        return self

    @property
    def gas_price(self) -> int | None:
        """Return the gas price."""
        return self._gas_price

    def set_gas_price(self, gas_price: int) -> Self:
        """
        Set the gas price for the call.

        Args:
            gas_price: The gas price.

        Returns:
            This query instance.

        Raises:
            TypeError: If gas_price is not an integer.
            ValueError: If gas_price is negative.
        """
        self._gas_price = _validate_non_negative_int(gas_price, "gas_price")
        return self

    @property
    def block_number(self) -> int | None:
        """Return the block number, or None for the latest block."""
        return self._block_number

    def set_block_number(self, block_number: int) -> Self:
        """
        Set the block whose state the call runs against.

        Defaults to the latest block.

        Args:
            block_number: The block number.

        Returns:
            This query instance.

        Raises:
            TypeError: If block_number is not an integer.
            ValueError: If block_number is negative.
        """
        self._block_number = _validate_non_negative_int(block_number, "block_number")
        return self

    # Retry

    @property
    def max_attempts(self) -> int:
        """Return the maximum number of request attempts."""
        return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> Self:
        """
        Set the maximum number of HTTP request attempts.

        The initial request counts as the first attempt.

        Args:
            max_attempts: Maximum number of attempts. Must be at least 1.

        Returns:
            This query instance.

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

    def set_max_backoff(self, max_backoff: int | float) -> Self:
        """
        Set the maximum delay between retry attempts.

        Args:
            max_backoff: Maximum retry delay in seconds. Must be at least 0.5.

        Returns:
            This query instance.

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

    # Execution

    @abstractmethod
    def execute(self, client: Client, timeout: int | float | None = None) -> Any:
        """Execute the query against the client's mirror node."""

    def _build_payload(self) -> dict[str, Any]:
        """
        Build the JSON body for ``POST /contracts/call``.

        Raises:
            ValueError: If neither a contract ID nor a contract EVM address is set.
        """
        if self._contract_evm_address is not None:
            contract_address = self._contract_evm_address
        elif self._contract_id is not None:
            contract_address = self._contract_id.to_evm_address()
        else:
            raise ValueError(f"contract_id or contract_evm_address must be set before executing {type(self).__name__}")

        payload: dict[str, Any] = {}

        # The mirror node rejects an empty "0x", so empty call data is left out.
        if self._function_parameters:
            payload["data"] = "0x" + self._function_parameters.hex()

        payload["to"] = "0x" + contract_address

        sender_address = self._sender_evm_address
        if sender_address is None and self._sender is not None:
            sender_address = self._sender.to_evm_address()
        if sender_address is not None:
            payload["from"] = "0x" + sender_address

        if self._gas_limit is not None:
            payload["gas"] = self._gas_limit
        if self._gas_price is not None:
            payload["gasPrice"] = self._gas_price
        if self._value is not None:
            payload["value"] = self._value

        # Block numbers are sent as hex quantities, as in eth_call.
        payload["block"] = "latest" if self._block_number is None else hex(self._block_number)
        payload["estimate"] = self._ESTIMATE

        return payload

    def _build_url(self, client: Client) -> str:
        """Build the ``/contracts/call`` endpoint URL."""
        base_url = to_web3_rest_url(client.network.get_mirror_rest_url().rstrip("/"))
        return f"{base_url}/contracts/call"

    def _call_mirror_node(self, client: Client, timeout: int | float | None) -> str:
        """
        Send the request and return the hex ``result`` field.

        Raises:
            ValueError: If the query is not configured, or the response is malformed.
            TypeError: If an argument has an invalid type.
            MirrorNodeError: If the mirror node returns an error status.
            RuntimeError: If retries or the total deadline are exhausted.
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

        # Validate before any network call.
        payload = self._build_payload()

        response = send_with_retry(
            "POST",
            self._build_url(client),
            timeout=timeout,
            max_attempts=self._max_attempts,
            max_backoff=self._max_backoff,
            retryable_statuses=_RETRYABLE_HTTP_STATUSES,
            json_body=payload,
            description=type(self).__name__,
        )

        if response.status_code != 200:
            raise mirror_node_error_from_response(response)

        try:
            body = response.json()
        except ValueError as exc:
            raise ValueError("Mirror Node returned a malformed JSON response") from exc

        result = body.get("result") if isinstance(body, dict) else None
        if not isinstance(result, str) or not _HEX_RESULT_PATTERN.fullmatch(result):
            raise ValueError("Mirror Node returned a malformed JSON response: missing hex 'result'")

        return result

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"contract_id={self._contract_id}, "
            f"contract_evm_address={self._contract_evm_address}, "
            f"sender={self._sender}, "
            f"sender_evm_address={self._sender_evm_address}, "
            f"function_parameters={self._function_parameters.hex() if self._function_parameters else None}, "
            f"value={self._value}, "
            f"gas_limit={self._gas_limit}, "
            f"gas_price={self._gas_price}, "
            f"block_number={self._block_number})"
        )

    __str__ = __repr__


def _normalize_evm_address(address: str, name: str) -> str:
    """Return a 20-byte EVM address as 40 lowercase hex characters without a ``0x`` prefix."""
    if not isinstance(address, str):
        raise TypeError(f"{name} must be a string")

    stripped = address.strip()
    if stripped[:2].lower() == "0x":
        stripped = stripped[2:]

    if not _EVM_ADDRESS_PATTERN.fullmatch(stripped):
        raise ValueError(f"{name} must be 20 bytes of hex (40 characters), with an optional 0x prefix")

    return stripped.lower()


def _validate_non_negative_int(value: int, name: str) -> int:
    """Return value if it is a non-negative int, otherwise raise."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")

    if value < 0:
        raise ValueError(f"{name} must not be negative")

    return value
