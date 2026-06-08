from __future__ import annotations

from dataclasses import dataclass

from tck.util.param_utils import to_bool


@dataclass
class CustomFeeParams:
    """Parameters for a custom fee in topic creation."""

    feeCollectorAccountId: str | None = None
    feeCollectorsExempt: bool | None = None
    fixedFee: FixedFeeParams | None = None
    fractionalFee: FractionalFeeParams | None = None
    royaltyFee: RoyaltyFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CustomFeeParams:
        fixed_fee = params.get("fixedFee")
        fee_collector_account_id = params.get("feeCollectorAccountId")

        return cls(
            feeCollectorAccountId=fee_collector_account_id,
            feeCollectorsExempt=to_bool(params.get("feeCollectorsExempt")),
            fixedFee=(FixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
        )


@dataclass
class FixedFeeParams:
    """Parameters for a fixed fee custom fee in topic creation."""

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
    numerator: str | None = None
    denominator: str | None = None
    fallbackFee: FixedFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> RoyaltyFeeParams:
        fixed_fee = params.get("fixedFee")

        return (
            cls(
                numerator=params.get("numerator"),
                denominator=params.get("denominator"),
                fixedFee=(FixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
            ),
        )


@dataclass
class CustomFeeLimitParams:
    accountId: str | None = None
    fixedFee: FixedFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CustomFeeLimitParams:
        fixed_fee = params.get("fixedFee")

        return (
            cls(
                accountId=params.get("accountId"),
                fixedFee=(FixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
            ),
        )
