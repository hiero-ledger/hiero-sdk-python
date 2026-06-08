from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.param.custom_fee import CustomFeeLimitParams, CustomFeeParams
from tck.util.param_utils import (
    non_empty_string_list,
    non_empty_string_or_none,
    parse_common_transaction_params,
    parse_session_id,
    to_int,
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
    customFees: list[CustomFeeParams] | None = None

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
                [CustomFeeParams.parse_json_params(custom_fee) for custom_fee in custom_fees]
                if custom_fees is not None
                else None
            ),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class TopicMessageSubmitParams(BaseTransactionParams):
    """Request parameters for submitTopicMessage endpoint."""

    topicId: str | None = None
    message: str | None = None
    maxChunks: int | None = None
    chunkSize: int | None = None
    customFeeLimits: list[CustomFeeLimitParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> TopicMessageSubmitParams:

        custom_fee_limits = params.get("customFeeLimits")
        if custom_fee_limits is not None and not isinstance(custom_fee_limits, list):
            raise ValueError("customFeeLimits must be a list")
        if custom_fee_limits is not None and any(not isinstance(custom_fee, dict) for custom_fee in custom_fee_limits):
            raise ValueError("each customFeeLimits item must be an object")

        return cls(
            topicId=params.get("topicId"),
            message=params.get("message"),
            maxChunks=to_int(params.get("maxChunks")),
            chunkSize=to_int(params.get("chunkSize")),
            customFeeLimits=(
                [CustomFeeLimitParams.parse_json_params(custom_fee_limit) for custom_fee_limit in custom_fee_limits]
                if custom_fee_limits is not None
                else None
            ),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
