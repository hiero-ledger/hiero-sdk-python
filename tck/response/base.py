"""TCK common response models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatusOnlyResponse:
    """Common response payload for endpoints that return only a status."""

    status: str | None = None
