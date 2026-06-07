"""TCK request parameter models for approveAllowance endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
)


@dataclass
class HbarAllowanceParams:
    """Nested hbar allowance parameters."""

    amount: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> HbarAllowanceParams:
        return cls(amount=params.get("amount"))


@dataclass
class TokenAllowanceParams:
    """Nested token allowance parameters."""

    tokenId: str | None = None
    amount: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> TokenAllowanceParams:
        return cls(
            tokenId=params.get("tokenId"),
            amount=params.get("amount"),
        )


@dataclass
class NftAllowanceParams:
    """Nested NFT allowance parameters."""

    tokenId: str | None = None
    serialNumbers: list[str] | None = None
    approvedForAll: bool | None = None
    delegateSpenderAccountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> NftAllowanceParams:
        return cls(
            tokenId=params.get("tokenId"),
            serialNumbers=params.get("serialNumbers"),
            approvedForAll=to_bool(params.get("approvedForAll")),
            delegateSpenderAccountId=params.get("delegateSpenderAccountId"),
        )


@dataclass
class AllowanceEntry:
    """A single allowance entry in the allowances list."""

    ownerAccountId: str | None = None
    spenderAccountId: str | None = None
    hbar: HbarAllowanceParams | None = None
    token: TokenAllowanceParams | None = None
    nft: NftAllowanceParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> AllowanceEntry:
        hbar = params.get("hbar")
        token = params.get("token")
        nft = params.get("nft")

        return cls(
            ownerAccountId=params.get("ownerAccountId"),
            spenderAccountId=params.get("spenderAccountId"),
            hbar=HbarAllowanceParams.parse_json_params(hbar) if hbar is not None else None,
            token=TokenAllowanceParams.parse_json_params(token) if token is not None else None,
            nft=NftAllowanceParams.parse_json_params(nft) if nft is not None else None,
        )


@dataclass
class ApproveAllowanceParams(BaseTransactionParams):
    """Request parameters for the approveAllowance endpoint."""

    allowances: list[AllowanceEntry] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> ApproveAllowanceParams:
        """Parse JSON-RPC params into an ApproveAllowanceParams instance."""
        raw_allowances = params.get("allowances")
        allowances = None
        if raw_allowances is not None:
            allowances = [AllowanceEntry.parse_json_params(entry) for entry in raw_allowances]

        return cls(
            allowances=allowances,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
