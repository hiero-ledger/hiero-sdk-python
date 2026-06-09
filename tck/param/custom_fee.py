from __future__ import annotations

from dataclasses import dataclass

from tck.util.param_utils import to_bool


@dataclass
class CustomFeeParams:
    """Request parameters for CustomFee."""

    feeCollectorAccountId: str | None = None
    feeCollectorsExempt: bool | None = None
    fixedFee: FixedFeeParams | None = None
    fractionalFee: FractionalFeeParams | None = None
    royaltyFee: RoyaltyFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CustomFeeParams:
        """Parse JSON-RPC params into a CustomFeeParams instance."""
        fixed_fee = params.get("fixedFee")
        fee_collector_account_id = params.get("feeCollectorAccountId")

        return cls(
            feeCollectorAccountId=fee_collector_account_id,
            feeCollectorsExempt=to_bool(params.get("feeCollectorsExempt")),
            fixedFee=(FixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
        )


@dataclass
class FixedFeeParams:
    """Request parameters for FixedFee."""

    amount: str | None = None
    denominatingTokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FixedFeeParams:
        """Parse JSON-RPC params into a FixedFeeParams instance."""
        return cls(
            amount=params.get("amount"),
            denominatingTokenId=params.get("denominatingTokenId"),
        )


@dataclass
class FractionalFeeParams:
    """Request parameters for FractionalFee."""

    numerator: str | None = None
    denominator: str | None = None
    minimumAmount: str | None = None
    maximumAmount: str | None = None
    assessmentMethod: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FractionalFeeParams:
        """Parse JSON-RPC params into a FractionalFeeParams instance."""
        return cls(
            numerator=params.get("numerator"),
            denominator=params.get("denominator"),
            minimumAmount=params.get("minimumAmount"),
            maximumAmount=params.get("maximumAmount"),
            assessmentMethod=params.get("assessmentMethod"),
        )


@dataclass
class RoyaltyFeeParams:
    """Request parameters for RoyaltyFee."""

    numerator: str | None = None
    denominator: str | None = None
    fallbackFee: FixedFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> RoyaltyFeeParams:
        """Parse JSON-RPC params into a RoyaltyFeeParams instance."""
        fixed_fee = params.get("fixedFee")

        return cls(
            numerator=params.get("numerator"),
            denominator=params.get("denominator"),
            fixedFee=(FixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
        )


@dataclass
class CustomFeeLimitParams:
    """Request parameters for CustomFeeLimit."""

    payerId: str | None = None
    fixedFees: list[FixedFeeParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CustomFeeLimitParams:
        """Parse JSON-RPC params into a CustomFeeLimitParams instance."""
        fixed_fees = params.get("fixedFees")

        return cls(
            payerId=params.get("payerId"),
            fixedFees=(
                [FixedFeeParams.parse_json_params(fixed_fee) for fixed_fee in fixed_fees]
                if fixed_fees is not None
                else None
            ),
        )
