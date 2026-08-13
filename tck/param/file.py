from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_common_transaction_params, parse_session_id


@dataclass
class CreateFileParams(BaseTransactionParams):
    """Parameters for creating a file. Extends BaseTransactionParams to include common transaction parameters."""

    keys: list[str] | None = None
    contents: str | None = None
    expirationTime: str | None = None
    memo: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateFileParams:
        keys = params.get("keys")
        if keys is not None:
            if not isinstance(keys, list):
                raise ValueError("keys must be a list")
            for key in keys:
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("keys must be a list of non-empty strings")

        return cls(
            keys=keys,
            contents=params.get("contents"),
            expirationTime=params.get("expirationTime"),
            memo=params.get("memo"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class DeleteFileParams(BaseTransactionParams):
    """Parameters for deleting a file. Extends BaseTransactionParams to include common transaction parameters."""

    fileId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteFileParams:
        """Parse JSON-RPC params into a DeleteFileParams instance."""
        # Spec's input table says "fileID" but every property test, the JSON
        # example, and the JS reference handler use "fileId".
        return cls(
            fileId=params.get("fileId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
