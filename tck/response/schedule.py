from __future__ import annotations

from dataclasses import dataclass

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
    signers: list[str] | None = None
    adminKey: str | None = None
    expirationTime: str | None = None
    executedAt: str | None = None
    deletedAt: str | None = None
    scheduleMemo: str | None = None
    waitForExpiry: bool | None = None
    cost: str | None = None
