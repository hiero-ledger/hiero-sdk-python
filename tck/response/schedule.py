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
