"""TCK response models for node endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NodeResponse:
    """Represent the response for all the node related transaction."""

    nodeId: str | None = None
    status: str | None = None
