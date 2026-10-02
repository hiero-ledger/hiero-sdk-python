from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseParams
from tck.util.param_utils import parse_session_id


@dataclass
class SetupParams(BaseParams):
    operatorAccountId: str = None
    operatorPrivateKey: str = None
    nodeIp: str | None = None
    nodeAccountId: str | None = None
    mirrorNetworkIp: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> SetupParams:
        return cls(
            operatorAccountId=params.get("operatorAccountId"),
            operatorPrivateKey=params.get("operatorPrivateKey"),
            nodeIp=params.get("nodeIp"),
            nodeAccountId=params.get("nodeAccountId"),
            mirrorNetworkIp=params.get("mirrorNetworkIp"),
            sessionId=parse_session_id(params),
        )


@dataclass
class PingParams(BaseParams):
    nodeAccountId: str = None

    @classmethod
    def parse_json_params(cls, params: dict) -> PingParams:
        if not isinstance(params, dict):
            raise TypeError("params must be an object")

        node_account_id = params.get("nodeAccountId")
        if not isinstance(node_account_id, str) or not node_account_id.strip():
            raise ValueError("nodeAccountId is required and must be a non-empty string")

        return cls(nodeAccountId=node_account_id, sessionId=parse_session_id(params))
