from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    non_empty_string_list,
    non_empty_string_or_none,
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
    to_int,
)


@dataclass
class CreateTopicFixedFeeParams:
    """Parameters for a fixed fee custom fee in topic creation."""

    amount: int | None = None
    denominatingTokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTopicFixedFeeParams:
        return cls(
            amount=to_int(params.get("amount")),
            denominatingTokenId=non_empty_string_or_none(params.get("denominatingTokenId")),
        )


@dataclass
class CreateTopicCustomFeeParams:
    """Parameters for a custom fee in topic creation."""

    feeCollectorAccountId: str | None = None
    feeCollectorsExempt: bool | None = None
    fixedFee: CreateTopicFixedFeeParams | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTopicCustomFeeParams:
        fixed_fee = params.get("fixedFee")

        fee_collector_account_id = params.get("feeCollectorAccountId")
        if isinstance(fee_collector_account_id, str):
            fee_collector_account_id = fee_collector_account_id.strip()

        return cls(
            feeCollectorAccountId=fee_collector_account_id,
            feeCollectorsExempt=to_bool(params.get("feeCollectorsExempt")),
            fixedFee=(CreateTopicFixedFeeParams.parse_json_params(fixed_fee) if isinstance(fixed_fee, dict) else None),
        )


@dataclass
class CreateTopicParams(BaseTransactionParams):
    """Parameters for creating a topic. Extends BaseTransactionParams to include common transaction parameters."""

    memo: str | None = None
    adminKey: str | None = None
    submitKey: str | None = None
    autoRenewPeriod: int | None = None
    autoRenewAccountId: str | None = None
    feeScheduleKey: str | None = None
    feeExemptKeys: list[str] | None = None
    customFees: list[CreateTopicCustomFeeParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTopicParams:
        fee_exempt_keys = params.get("feeExemptKeys")
        if fee_exempt_keys is not None and not isinstance(fee_exempt_keys, list):
            raise ValueError("feeExemptKeys must be a list")

        custom_fees = params.get("customFees")
        if custom_fees is not None and not isinstance(custom_fees, list):
            raise ValueError("customFees must be a list")
        if custom_fees is not None and any(not isinstance(custom_fee, dict) for custom_fee in custom_fees):
            raise ValueError("each customFees item must be an object")
        return cls(
            memo=params.get("memo"),
            adminKey=non_empty_string_or_none(params.get("adminKey")),
            submitKey=non_empty_string_or_none(params.get("submitKey")),
            autoRenewPeriod=to_int(params.get("autoRenewPeriod")),
            autoRenewAccountId=non_empty_string_or_none(params.get("autoRenewAccountId")),
            feeScheduleKey=non_empty_string_or_none(params.get("feeScheduleKey")),
            feeExemptKeys=non_empty_string_list(fee_exempt_keys),
            customFees=(
                [CreateTopicCustomFeeParams.parse_json_params(custom_fee) for custom_fee in custom_fees]
                if custom_fees is not None
                else None
            ),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
