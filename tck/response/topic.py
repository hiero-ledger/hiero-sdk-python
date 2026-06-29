from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateTopicResponse:
    """Response payload for createTopic."""

    topicId: str | None = None
    status: str | None = None


@dataclass
class TopicMessageSubmitResponse:
    """Response payload for submitTopicMessage."""

    status: str | None = None
