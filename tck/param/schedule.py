from __future__ import annotations

from dataclasses import dataclass, field

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_common_transaction_params, parse_session_id, to_bool


@dataclass
class ScheduledTransactionParams:
    """The inner (schedulable) transaction of a createSchedule request."""

    method: str | None = None
    params: dict = field(default_factory=dict)

    @classmethod
    def parse_json_params(cls, params: dict) -> ScheduledTransactionParams:
        """Parse JSON-RPC params into a ScheduledTransactionParams instance."""
        if not isinstance(params, dict):
            raise ValueError("scheduledTransaction must be an object")

        method = params.get("method")
        if not isinstance(method, str) or not method.strip():
            raise ValueError("scheduledTransaction.method is required and must be a non-empty string")

        inner_params = params.get("params")
        if inner_params is None:
            inner_params = {}
        if not isinstance(inner_params, dict):
            raise ValueError("scheduledTransaction.params must be an object")

        return cls(method=method, params=inner_params)


@dataclass
class CreateScheduleParams(BaseTransactionParams):
    """Request parameters for the createSchedule endpoint."""

    scheduledTransaction: ScheduledTransactionParams | None = None
    memo: str | None = None
    adminKey: str | None = None
    payerAccountId: str | None = None
    expirationTime: str | None = None
    waitForExpiry: bool | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateScheduleParams:
        """Parse JSON-RPC params into a CreateScheduleParams instance."""
        scheduled_transaction = params.get("scheduledTransaction")

        return cls(
            scheduledTransaction=(
                ScheduledTransactionParams.parse_json_params(scheduled_transaction)
                if scheduled_transaction is not None
                else None
            ),
            memo=params.get("memo"),
            adminKey=params.get("adminKey"),
            payerAccountId=params.get("payerAccountId"),
            expirationTime=params.get("expirationTime"),
            waitForExpiry=to_bool(params.get("waitForExpiry")),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
