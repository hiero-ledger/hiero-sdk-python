from __future__ import annotations

from dataclasses import dataclass, field

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateScheduleResponse:
    """Response payload for createSchedule."""

    scheduleId: str | None = None
    transactionId: str | None = None
    status: str | None = None


@dataclass
class SignScheduleResponse(StatusOnlyResponse):
    """Response payload for signSchedule."""


@dataclass
class DeleteScheduleResponse(StatusOnlyResponse):
    """Response payload for deleteSchedule."""


@dataclass
class ScheduleInfoResponse:
    """Response payload for getScheduleInfo."""

    scheduleId: str | None = None
    creatorAccountId: str | None = None
    payerAccountId: str | None = None
    scheduledTransactionId: str | None = None
    signers: list[str] = field(default_factory=list)
    adminKey: str | None = field(metadata={"nullable": True}, default=None)
    expirationTime: str | None = None
    executedAt: str | None = field(metadata={"nullable": True}, default=None)
    deletedAt: str | None = field(metadata={"nullable": True}, default=None)
    scheduleMemo: str | None = None
    waitForExpiry: bool | None = None


@dataclass
class ScheduleInfoCostResponse:
    """Response payload for getScheduleInfo when getCost=true.

    Spec (getCost) and the JS TCK reference return only the cost field, so this
    is kept separate from ScheduleInfoResponse to avoid leaking its nullable
    fields (adminKey/executedAt/deletedAt) as spurious nulls.
    """

    cost: str | None = None
