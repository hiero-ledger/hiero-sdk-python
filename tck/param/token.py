"""TCK request parameter models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
    to_int,
)


@dataclass
class CreateTokenParams(BaseTransactionParams):
    """Request parameters for the createToken endpoint."""

    name: str | None = None
    symbol: str | None = None
    treasuryAccountId: str | None = None
    tokenType: str | None = None
    initialSupply: int | None = None
    decimals: int | None = None
    adminKey: str | None = None
    kycKey: str | None = None
    freezeKey: str | None = None
    wipeKey: str | None = None
    supplyKey: str | None = None
    pauseKey: str | None = None
    feeScheduleKey: str | None = None
    memo: str | None = None
    metadata: str | None = None
    metadataKey: str | None = None
    maxSupply: int | None = None
    supplyType: str | None = None
    freezeDefault: bool | None = None
    expirationTime: int | None = None
    autoRenewAccountId: str | None = None
    autoRenewPeriod: int | None = None
    customFees: list[dict] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTokenParams:
        """Parse JSON-RPC params into a CreateTokenParams instance."""
        return cls(
            name=params.get("name"),
            symbol=params.get("symbol"),
            treasuryAccountId=params.get("treasuryAccountId"),
            tokenType=params.get("tokenType"),
            initialSupply=to_int(params.get("initialSupply")),
            decimals=to_int(params.get("decimals")),
            adminKey=params.get("adminKey"),
            kycKey=params.get("kycKey"),
            freezeKey=params.get("freezeKey"),
            wipeKey=params.get("wipeKey"),
            supplyKey=params.get("supplyKey"),
            pauseKey=params.get("pauseKey"),
            feeScheduleKey=params.get("feeScheduleKey"),
            memo=params.get("memo"),
            metadata=params.get("metadata"),
            metadataKey=params.get("metadataKey"),
            maxSupply=to_int(params.get("maxSupply")),
            supplyType=params.get("supplyType"),
            freezeDefault=to_bool(params.get("freezeDefault")),
            expirationTime=to_int(params.get("expirationTime")),
            autoRenewAccountId=params.get("autoRenewAccountId"),
            autoRenewPeriod=to_int(params.get("autoRenewPeriod")),
            customFees=params.get("customFees"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
