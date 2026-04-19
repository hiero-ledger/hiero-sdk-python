from __future__ import annotations

from dataclasses import dataclass

from tck.util.key_utils import KeyType


@dataclass
class KeyGenerationParams:
    type: KeyType = None
    fromKey: str | None = None
    threshold: int | None = None
    keys: list[KeyGenerationParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> KeyGenerationParams:
        key_list = params.get("keys") or []

        return cls(
            type=(KeyType.from_string(params.get("type")) if params.get("type") else None),
            fromKey=params.get("fromKey"),
            threshold=params.get("threshold"),
            keys=[cls.parse_json_params(k) for k in key_list],
        )
