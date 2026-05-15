from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateTopicResponse:
    topicId: str | None = None
    status: str | None = None
