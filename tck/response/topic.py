from __future__ import annotations

from dataclasses import dataclass

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateTopicResponse:
    """Response payload for createTopic."""

    topicId: str | None = None
    status: str | None = None


@dataclass
class UpdateTopicResponse(StatusOnlyResponse):
    """Response payload for updateTopic."""

    status: str | None = None


@dataclass
class DeleteTopicResponse(StatusOnlyResponse):
    """Response payload for deleteTopic."""


@dataclass
class TopicMessageSubmitResponse:
    """Response payload for submitTopicMessage."""

    status: str | None = None


@dataclass
class TopicInfoResponse:
    """Response payload for getTopicInfo."""

    topicId: str | None = None
    topicMemo: str | None = None
    sequenceNumber: str | None = None
    runningHash: str | None = None
    adminKey: str | None = None
    submitKey: str | None = None
    autoRenewAccountId: str | None = None
    autoRenewPeriod: str | None = None
    expirationTime: str | None = None
    feeScheduleKey: str | None = None
    feeExemptKeys: list[str] | None = None
    customFees: list[CustomFeeResponse] = None
    ledgerId: str | None = None


@dataclass
class CustomFeeResponse:
    """Response for the CustomFee."""

    feeCollectorAccountId: str | None = None
    allCollectorsAreExempt: bool | None = None
    fixedFee: FixedFeeResponse | None = None


@dataclass
class FixedFeeResponse:
    """Response for the FixedFee."""

    amount: str | None = None
    denominatingTokenId: str | None = None
