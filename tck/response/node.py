"""TCK responses for node service methods."""

from __future__ import annotations

from dataclasses import dataclass

from tck.response.base import StatusOnlyResponse


@dataclass
class DeleteNodeResponse(StatusOnlyResponse):
    """Response returned by the deleteNode JSON-RPC method."""

    pass
