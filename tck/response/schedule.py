from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateScheduleResponse:
    """Response payload for createSchedule."""

    scheduleId: str | None = None
    transactionId: str | None = None
    status: str | None = None
