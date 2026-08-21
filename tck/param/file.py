from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseParams, BaseTransactionParams
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
class GetFileContentsParams(BaseParams):
    """Parameters for getting a file's contents."""

    fileId: str | None = None
    queryPayment: str | None = None
    maxQueryPayment: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> GetFileContentsParams:
        return cls(
            sessionId=parse_session_id(params),
            fileId=params.get("fileId"),
            queryPayment=params.get("queryPayment"),
            maxQueryPayment=params.get("maxQueryPayment"),
        )


@dataclass
class DeleteFileParams(BaseTransactionParams):
    """Parameters for deleting a file. Extends BaseTransactionParams to include common transaction parameters."""

    fileId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteFileParams:
        # Spec documents the key as fileID (capital ID). Bind it verbatim so the
        # driver parameter maps correctly. Do not "fix" this to fileId.
        return cls(
            fileId=params.get("fileID"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
