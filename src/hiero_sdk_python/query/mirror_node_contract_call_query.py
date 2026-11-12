"""
Mirror Node Contract Call Query.

Simulates a contract call on the mirror node (``eth_call`` semantics) and
returns the raw ABI-encoded result. Unlike ContractCallQuery, it is free:
there is no query payment and no consensus node round trip.
"""

from __future__ import annotations

from typing import ClassVar

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.query.mirror_node_contract_query import MirrorNodeContractQuery


class MirrorNodeContractCallQuery(MirrorNodeContractQuery):
    """
    Simulate a contract call on the mirror node and return the ABI-encoded result.

    Uses ``POST /api/v1/contracts/call``. The call is never submitted to the
    network, so it changes no state, even for a state-changing function.

    The result is the raw hex returned by the contract. To decode it, wrap the
    bytes in a ContractFunctionResult::

        result_hex = (
            MirrorNodeContractCallQuery()
            .set_contract_id(contract_id)
            .set_function("getMessage")
            .execute(client)
        )
        message = ContractFunctionResult(
            contract_call_result=bytes.fromhex(result_hex[2:])
        ).get_bytes32(0)

    A call that reverts raises MirrorNodeError, whose messages include the
    revert reason.

    Results are not read-after-write consistent: the mirror node lags
    consensus by a few seconds. Until it imports a newly created contract,
    a query does not fail. It runs against an address with no code, so a
    call returns ``"0x"`` and a gas estimate is only the cost of a plain
    transfer, too low for the real call. Right after a
    ``ContractCreateTransaction`` or ``ContractExecuteTransaction``, wait
    until the mirror node returns the expected state before relying on a
    result.
    """

    _ESTIMATE: ClassVar[bool] = False

    def execute(self, client: Client, timeout: int | float | None = None) -> str:
        """
        Execute the query and return the hex-encoded call result.

        Args:
            client: The client used to determine the mirror node URL.
            timeout: Total deadline in seconds for the whole call, including
                retries and backoff. Each HTTP attempt is bounded by
                min(30, remaining time). Defaults to the client's request timeout.

        Returns:
            The ABI-encoded result as a ``0x``-prefixed hex string.

        Raises:
            ValueError: If no contract is set, timeout is not positive, or the
                response is malformed.
            TypeError: If an argument has an invalid type.
            MirrorNodeError: If the mirror node returns an error status, for
                example when the call reverts.
            RuntimeError: If retries or the total deadline are exhausted.
        """
        return self._call_mirror_node(client, timeout)
