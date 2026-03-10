from dataclasses import dataclass

from tck.param.common_tx_param import CommonTransactionParams
from tck.util.json_param_parser import parse_session_id


@dataclass
class BaseParams:
  sessionId: str = None

  @classmethod
  def from_dict(cls, params: dict) -> "BaseParams":
    return cls(parse_session_id(params))


@dataclass
class BaseTransactionParams(BaseParams):
  commonTransactionParams: CommonTransactionParams = None

