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
class FixedFeeParams:
    """Fixed custom fee parameters."""

    amount: str | None = None
    denominatingTokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FixedFeeParams:
        return cls(
            amount=params.get("amount"),
            denominatingTokenId=params.get("denominatingTokenId"),
        )


@dataclass
class FractionalFeeParams:
    """Fractional custom fee parameters."""

    numerator: str | None = None
    denominator: str | None = None
    minimumAmount: str | None = None
    maximumAmount: str | None = None
    assessmentMethod: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FractionalFeeParams:
        return cls(
            numerator=params.get("numerator"),
            denominator=params.get("denominator"),
            minimumAmount=params.get("minimumAmount"),
            maximumAmount=params.get("maximumAmount"),
            assessmentMethod=params.get("assessmentMethod"),
        )


@dataclass
class RoyaltyFeeParams:
    """Royalty custom fee parameters."""

    numerator: str | None = None
    denominator: str | None = None
    fallbackFee: FixedFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> RoyaltyFeeParams:
        fallback_fee = params.get("fallbackFee")
        if fallback_fee is not None and not isinstance(fallback_fee, dict):
            raise ValueError("fallbackFee must be an object")

        return cls(
            numerator=params.get("numerator"),
            denominator=params.get("denominator"),
            fallbackFee=FixedFeeParams.parse_json_params(fallback_fee) if fallback_fee is not None else None,
        )


@dataclass
class CustomFeeParams:
    """Token custom fee parameters."""

    feeCollectorAccountId: str | None = None
    feeCollectorsExempt: bool | None = None
    fixedFee: FixedFeeParams | None = None
    fractionalFee: FractionalFeeParams | None = None
    royaltyFee: RoyaltyFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CustomFeeParams:
        if not isinstance(params, dict):
            raise ValueError("each customFees item must be an object")

        fee_values = {
            "fixedFee": params.get("fixedFee"),
            "fractionalFee": params.get("fractionalFee"),
            "royaltyFee": params.get("royaltyFee"),
        }
        present_fees = [name for name, value in fee_values.items() if value is not None]
        if len(present_fees) != 1:
            raise ValueError("custom fee must contain exactly one fee type")
        if not isinstance(fee_values[present_fees[0]], dict):
            raise ValueError(f"{present_fees[0]} must be an object")

        return cls(
            feeCollectorAccountId=params.get("feeCollectorAccountId"),
            feeCollectorsExempt=to_bool(params.get("feeCollectorsExempt")),
            fixedFee=(
                FixedFeeParams.parse_json_params(fee_values["fixedFee"]) if fee_values["fixedFee"] is not None else None
            ),
            fractionalFee=(
                FractionalFeeParams.parse_json_params(fee_values["fractionalFee"])
                if fee_values["fractionalFee"] is not None
                else None
            ),
            royaltyFee=(
                RoyaltyFeeParams.parse_json_params(fee_values["royaltyFee"])
                if fee_values["royaltyFee"] is not None
                else None
            ),
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
    customFees: list[CustomFeeParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTokenParams:
        """Parse JSON-RPC params into a CreateTokenParams instance."""
        custom_fees = params.get("customFees")
        if custom_fees is not None and not isinstance(custom_fees, list):
            raise ValueError("customFees must be a list")

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
            customFees=(
                [CustomFeeParams.parse_json_params(custom_fee) for custom_fee in custom_fees]
                if custom_fees is not None
                else None
            ),
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
        metadata = params.get("metadata")
        if metadata is not None and not isinstance(metadata, list):
            raise ValueError("metadata must be a list")
        if metadata is not None and any(not isinstance(value, str) for value in metadata):
            raise ValueError("each metadata item must be a string")

        return cls(
            tokenId=params.get("tokenId"),
            amount=params.get("amount"),
            metadata=metadata,
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
        token_ids = params.get("tokenIds")
        if token_ids is not None and not isinstance(token_ids, list):
            raise ValueError("tokenIds must be a list")
        if token_ids is not None and any(not isinstance(token_id, str) for token_id in token_ids):
            raise ValueError("each tokenIds item must be a string")

        return cls(
            accountId=params.get("accountId"),
            tokenIds=token_ids,
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
