from dataclasses import dataclass

from tck.param.common import CommonTransactionParams
from tck.util.param_utils import parse_session_id


@dataclass
class BaseParams:
    sessionId: str = None

    @classmethod
    def parse_json_params(cls, params: dict) -> BaseParams:
        return cls(parse_session_id(params))


@dataclass
class BaseTransactionParams(BaseParams):
    commonTransactionParams: CommonTransactionParams | None = None
