"""
Mirror Node Contract Estimate Gas Query.

Asks the mirror node how much gas a call to a deployed contract needs, so
that a ContractExecuteTransaction can be given a gas limit before it is
submitted. The target must be an existing contract, so this does not
estimate the gas for deploying one.
"""

from __future__ import annotations

from typing import ClassVar

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.query.mirror_node_contract_query import MirrorNodeContractQuery


class MirrorNodeContractEstimateGasQuery(MirrorNodeContractQuery):
    """
    Estimate the gas a contract call needs, using the mirror node.

    Uses ``POST /api/v1/contracts/call`` with ``estimate`` set. It is free:
    there is no query payment and no consensus node round trip::

        gas = (
            MirrorNodeContractEstimateGasQuery()
            .set_contract_id(contract_id)
            .set_sender(operator_id)
            .set_function("setMessage", ContractFunctionParameters().add_bytes32(message))
            .execute(client)
        )
        ContractExecuteTransaction().set_contract_id(contract_id).set_gas(gas) ...

    Set the sender when the function checks ``msg.sender``, otherwise the
    simulation can revert. A call that reverts raises MirrorNodeError, whose
    messages include the revert reason.

    Results are not read-after-write consistent: the mirror node lags
    consensus by a few seconds. Until it imports a newly created contract,
    a query does not fail. It runs against an address with no code, so a
    call returns ``"0x"`` and a gas estimate is only the cost of a plain
    transfer, too low for the real call. Right after a
    ``ContractCreateTransaction`` or ``ContractExecuteTransaction``, wait
    until the mirror node returns the expected state before relying on a
    result.
    """

    _ESTIMATE: ClassVar[bool] = True

    def execute(self, client: Client, timeout: int | float | None = None) -> int:
        """
        Execute the query and return the estimated gas.

        Args:
            client: The client used to determine the mirror node URL.
            timeout: Total deadline in seconds for the whole call, including
                retries and backoff. Each HTTP attempt is bounded by
                min(30, remaining time). Defaults to the client's request timeout.

        Returns:
            The estimated gas.

        Raises:
            ValueError: If no contract is set, timeout is not positive, or the
                response is malformed.
            TypeError: If an argument has an invalid type.
            MirrorNodeError: If the mirror node returns an error status, for
                example when the call reverts.
            RuntimeError: If retries or the total deadline are exhausted.
        """
        result = self._call_mirror_node(client, timeout)

        try:
            return int(result, 16)
        except ValueError as exc:
            raise ValueError(f"Mirror Node returned a malformed gas estimate: {result!r}") from exc
