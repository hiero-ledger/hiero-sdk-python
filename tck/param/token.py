"""TCK request parameter models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
)


@dataclass
class CreateTokenParams(BaseTransactionParams):
    """Request parameters for the createToken endpoint."""

    name: str | None = None
    symbol: str | None = None
    decimals: int | None = None
    initialSupply: str | None = None
    treasuryAccountId: str | None = None
    adminKey: str | None = None
    kycKey: str | None = None
    freezeKey: str | None = None
    wipeKey: str | None = None
    supplyKey: str | None = None
    pauseKey: str | None = None
    feeScheduleKey: str | None = None
    metadataKey: str | None = None
    memo: str | None = None
    tokenType: str | None = None
    supplyType: str | None = None
    maxSupply: str | None = None
    freezeDefault: bool | None = None
    expirationTime: str | None = None
    autoRenewAccountId: str | None = None
    autoRenewPeriod: str | None = None
    metadata: str | None = None
    customFees: list[dict] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTokenParams:
        """Parse JSON-RPC params into a CreateTokenParams instance."""
        return cls(
            name=params.get("name"),
            symbol=params.get("symbol"),
            decimals=params.get("decimals"),
            initialSupply=params.get("initialSupply"),
            treasuryAccountId=params.get("treasuryAccountId"),
            adminKey=params.get("adminKey"),
            kycKey=params.get("kycKey"),
            freezeKey=params.get("freezeKey"),
            wipeKey=params.get("wipeKey"),
            supplyKey=params.get("supplyKey"),
            pauseKey=params.get("pauseKey"),
            feeScheduleKey=params.get("feeScheduleKey"),
            metadataKey=params.get("metadataKey"),
            memo=params.get("memo"),
            tokenType=params.get("tokenType"),
            supplyType=params.get("supplyType"),
            maxSupply=params.get("maxSupply"),
            freezeDefault=to_bool(params.get("freezeDefault")),
            expirationTime=params.get("expirationTime"),
            autoRenewAccountId=params.get("autoRenewAccountId"),
            autoRenewPeriod=params.get("autoRenewPeriod"),
            metadata=params.get("metadata"),
            customFees=params.get("customFees"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class MintTokenParams(BaseTransactionParams):
    """Request parameters for the mintToken endpoint."""

    tokenId: str | None = None
    amount: str | None = None
    metadata: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> MintTokenParams:
        """Parse JSON-RPC params into a MintTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            amount=params.get("amount"),
            metadata=params.get("metadata"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class AssociateTokenParams(BaseTransactionParams):
    """Request parameters for the associateToken endpoint."""

    accountId: str | None = None
    tokenIds: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> AssociateTokenParams:
        """Parse JSON-RPC params into an AssociateTokenParams instance."""
        return cls(
            accountId=params.get("accountId"),
            tokenIds=params.get("tokenIds"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class DeleteTokenParams(BaseTransactionParams):
    """Request parameters for the deleteToken endpoint."""

    tokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteTokenParams:
        """Parse JSON-RPC params into a DeleteTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class FreezeTokenParams(BaseTransactionParams):
    """Request parameters for the freezeToken endpoint."""

    tokenId: str | None = None
    accountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FreezeTokenParams:
        """Parse JSON-RPC params into a FreezeTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            accountId=params.get("accountId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class PauseTokenParams(BaseTransactionParams):
    """Request parameters for the pauseToken endpoint."""

    tokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> PauseTokenParams:
        """Parse JSON-RPC params into a PauseTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
