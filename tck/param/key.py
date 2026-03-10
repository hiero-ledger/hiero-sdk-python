from dataclasses import dataclass
from typing import List

from tck.param.base import BaseParams
from tck.util.json_param_parser import parse_session_id
from tck.util.key_utils import KeyType


@dataclass
class KeyGenerationParams(BaseParams):
  type: KeyType = None
  fromKey: str | None = None
  threshold: int | None = None
  keys: List["KeyGenerationParams"] | None = None

  @classmethod
  def from_dict(cls, params: dict) -> "KeyGenerationParams":
    key_list = params.get("keys")
    
    return cls(
      type = KeyType.from_string(params.get("type")),
      fromKey = params.get("fromKey"),
      threshold = params.get("threshold"),
      keys = [cls.from_dict(key) for key in key_list] if key_list else None,
      sessionId = parse_session_id(params)
    )
