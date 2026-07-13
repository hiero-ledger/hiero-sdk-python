"""TCK response models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateTokenResponse:
    """Response payload for createToken."""

    tokenId: str | None = None
    status: str | None = None


@dataclass
class MintTokenResponse:
    """Response payload for mintToken."""

    newTotalSupply: str | None = None
    serialNumbers: list[str] | None = None
    status: str | None = None


@dataclass
class AssociateTokenResponse(StatusOnlyResponse):
    """Response payload for associateToken."""


@dataclass
class DeleteTokenResponse(StatusOnlyResponse):
    """Response payload for deleteToken."""


@dataclass
class DissociateTokenResponse(StatusOnlyResponse):
    """Response payload for dissociateToken."""


@dataclass
class FreezeTokenResponse(StatusOnlyResponse):
    """Response payload for freezeToken."""


@dataclass
class GrantTokenKycResponse(StatusOnlyResponse):
    """Response payload for grantTokenKyc."""


@dataclass
class RevokeTokenKycResponse(StatusOnlyResponse):
    """Response payload for revokeTokenKyc."""


@dataclass
class RejectTokenResponse(StatusOnlyResponse):
    """Response payload for rejectToken."""


@dataclass
class PauseTokenResponse(StatusOnlyResponse):
    """Response payload for pauseToken."""


@dataclass
class AirdropTokenResponse(StatusOnlyResponse):
    """Response payload for airdropToken."""


@dataclass
class ClaimTokenResponse(StatusOnlyResponse):
    """Response payload for claimToken."""


@dataclass
class CustomFeeResponse:
    """Nested custom fee details for getTokenInfo."""

    fixedFee: dict | None = None
    fractionalFee: dict | None = None
    royaltyFee: dict | None = None
    feeCollectorAccountId: dict | None = None
    feeCollectorsExempt: bool | None = None


@dataclass
class GetTokenInfoResponse:
    """Response payload for getTokenInfo."""

    tokenId: str | None = None
    name: str | None = None
    symbol: str | None = None
    decimals: int | None = None
    totalSupply: str | None = None
    treasuryAccountId: str | None = None
    adminKey: str | None = None
    kycKey: str | None = None
    freezeKey: str | None = None
    pauseKey: str | None = None
    wipeKey: str | None = None
    supplyKey: str | None = None
    feeScheduleKey: str | None = None
    metadataKey: str | None = None
    defaultFreezeStatus: bool | None = field(metadata={"nullable": True}, default=None)
    defaultKycStatus: bool | None = field(metadata={"nullable": True}, default=None)
    pauseStatus: bool | None = field(metadata={"nullable": True}, default=None)
    isDeleted: bool | None = None
    autoRenewAccountId: str | None = None
    autoRenewPeriod: str | None = None
    expirationTime: str | None = None
    tokenMemo: str | None = None
    customFees: list[CustomFeeResponse] = field(default_factory=list)
    tokenType: str | None = None
    supplyType: str | None = None
    maxSupply: str | None = None
    metadata: str | None = None
    ledgerId: str | None = None


class WipeTokenResponse(StatusOnlyResponse):
    """Response payload for wipeToken."""
