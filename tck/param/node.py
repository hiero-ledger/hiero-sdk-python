"""TCK parameters for node service methods."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_session_id


@dataclass
class DeleteNodeParams(BaseTransactionParams):
    """Request parameters for the deleteNode endpoint."""

    nodeId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteNodeParams:
        """Parse JSON-RPC params into a DeleteNodeParams instance."""
        return cls(
            nodeId=params.get("nodeId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=cls._parse_common_transaction_params(params),
        )
