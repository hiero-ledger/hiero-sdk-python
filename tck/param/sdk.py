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
