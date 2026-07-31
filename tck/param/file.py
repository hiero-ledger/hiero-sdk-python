from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    non_empty_string_list,
    parse_common_transaction_params,
    parse_session_id,
    to_int,
)


@dataclass
class CreateFileParams(BaseTransactionParams):
    """Parameters for creating a file. Extends BaseTransactionParams to include common transaction parameters."""

    keys: list[str] | None = None
    contents: str | None = None
    expirationTime: int | None = None
    memo: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateFileParams:
        keys = params.get("keys")
        if keys is not None and not isinstance(keys, list):
            raise ValueError("keys must be a list")

        contents = params.get("contents")
        if contents is not None and not isinstance(contents, str):
            raise ValueError("contents must be a string")

        memo = params.get("memo")
        if memo is not None and not isinstance(memo, str):
            raise ValueError("memo must be a string")

        return cls(
            keys=non_empty_string_list(keys),
            contents=contents,
            expirationTime=to_int(params.get("expirationTime")),
            memo=memo,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
