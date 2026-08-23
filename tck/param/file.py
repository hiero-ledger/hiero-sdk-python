from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseParams, BaseTransactionParams
from tck.util.param_utils import (
    non_empty_string_or_none,
    parse_common_transaction_params,
    parse_session_id,
)


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
class UpdateFileParams(BaseTransactionParams):
    """Parameters for the updateFile JSON-RPC method.

    Extends BaseTransactionParams to inherit sessionId and
    commonTransactionParams from the base class.
    """

    fileId: str | None = None
    keys: list[str] | None = None
    contents: str | None = None
    expirationTime: str | None = None
    memo: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> UpdateFileParams:
        """Parse raw JSON-RPC params dict into an UpdateFileParams instance.

        Validates structural constraints (keys must be a list when present)
        and delegates sessionId/commonTransactionParams extraction to the
        shared utility helpers.  Individual key strings and expirationTime
        conversion are deferred to the handler layer.
        """
        keys = params.get("keys")
        if keys is not None:
            if not isinstance(keys, list):
                raise ValueError("keys must be a list")
            for key in keys:
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("keys must be a list of non-empty strings")

        contents_raw = params.get("contents")

        return cls(
            fileId=params.get("fileId"),
            keys=keys,
            # Per the spec, only the exact empty string ("") means "leave unchanged" (mapped to None).
            # Other values (including whitespace) are preserved verbatim.
            contents=None if contents_raw == "" else contents_raw,
            # expirationTime is kept as a raw string; int/Timestamp conversion
            # happens in the handler layer.
            expirationTime=params.get("expirationTime"),
            memo=params.get("memo"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
