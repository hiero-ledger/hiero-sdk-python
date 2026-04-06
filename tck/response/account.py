from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class CreateAccountResponse:
    accountId: str | None = None
    status: str | None = None


@dataclass
class StakingInfoResponse:
    declineStakingReward: bool | None = None
    stakePeriodStart: str | None = None
    pendingReward: str | None = None
    stakedToMe: str | None = None
    stakedAccountId: str | None = None
    stakedNodeId: str | None = None


@dataclass
class TokenRelationshipResponse:
    tokenId: str | None = None
    symbol: str | None = None
    balance: str | None = None
    kycStatus: str | None = None
    freezeStatus: str | None = None
    decimals: str | None = None
    automaticAssociation: bool | None = None


@dataclass
class GetAccountInfoResponse:
    accountId: str | None = None
    contractAccountId: str | None = None
    isDeleted: bool | None = None
    proxyAccountId: str | None = None
    proxyReceived: str | None = None
    key: str | None = None
    balance: str | None = None
    sendRecordThreshold: str | None = None
    receiveRecordThreshold: str | None = None
    isReceiverSignatureRequired: bool | None = None
    expirationTime: str | None = None
    autoRenewPeriod: str | None = None
    liveHashes: list[dict] = field(default_factory=list)
    tokenRelationships: dict[str, TokenRelationshipResponse] = field(default_factory=dict)
    accountMemo: str | None = None
    ownedNfts: str | None = None
    maxAutomaticTokenAssociations: str | None = None
    aliasKey: str | None = None
    ledgerId: str | None = None
    ethereumNonce: str | None = None
    hbarAllowances: list[dict] = field(default_factory=list)
    tokenAllowances: list[dict] = field(default_factory=list)
    nftAllowances: list[dict] = field(default_factory=list)
    stakingInfo: StakingInfoResponse | None = None
