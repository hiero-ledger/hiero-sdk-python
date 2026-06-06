"""TCK request parameter models for allowance endpoints."""

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


@dataclass
class DeleteAllowanceEntry:
    """A single allowance entry in the deleteAllowance allowances list."""

    ownerAccountId: str | None = None
    tokenId: str | None = None
    serialNumbers: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteAllowanceEntry:
        if not isinstance(params, dict):
            raise ValueError("each allowances item must be an object")

        if params.get("hbar") is not None or params.get("token") is not None:
            raise ValueError("deleteAllowance only supports NFT allowances")

        nft = params.get("nft")
        token_id = params.get("tokenId")
        serial_numbers = params.get("serialNumbers")

        if nft is not None:
            if not isinstance(nft, dict):
                raise ValueError("nft must be an object")
            token_id = nft.get("tokenId")
            serial_numbers = nft.get("serialNumbers")

        if token_id is not None and not isinstance(token_id, str):
            raise ValueError("tokenId must be a string")
        if serial_numbers is not None and not isinstance(serial_numbers, list):
            raise ValueError("serialNumbers must be a list")
        if serial_numbers is not None and any(not isinstance(serial, str) for serial in serial_numbers):
            raise ValueError("each serialNumbers item must be a string")

        owner_account_id = params.get("ownerAccountId")
        if owner_account_id is not None and not isinstance(owner_account_id, str):
            raise ValueError("ownerAccountId must be a string")

        return cls(
            ownerAccountId=owner_account_id,
            tokenId=token_id,
            serialNumbers=serial_numbers,
        )


@dataclass
class DeleteAllowanceParams(BaseTransactionParams):
    """Request parameters for the deleteAllowance endpoint."""

    allowances: list[DeleteAllowanceEntry] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteAllowanceParams:
        """Parse JSON-RPC params into a DeleteAllowanceParams instance."""
        raw_allowances = params.get("allowances")
        allowances = None
        if raw_allowances is not None:
            if not isinstance(raw_allowances, list):
                raise ValueError("allowances must be a list")
            allowances = [DeleteAllowanceEntry.parse_json_params(entry) for entry in raw_allowances]

        return cls(
            allowances=allowances,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
