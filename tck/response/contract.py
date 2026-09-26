from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.contract.contract_log_info import ContractLogInfo
from tck.response.base import StatusOnlyResponse


@dataclass
class CreateContractResponse:
    """Response payload for createContract."""

    contractId: str | None = None
    status: str | None = None


@dataclass
class DeleteContractResponse(StatusOnlyResponse):
    """Response payload for deleteContract."""


@dataclass
class ContractCallResponse:
    """Response payload for contractCallQuery."""

    contractId: str | None = None
    evmAddress: str | None = None
    errorMessage: str | None = None
    gasUsed: int | None = None
    logs: list[ContractLogInfo] = field(default_factory=list)
    gas: int | None = None
    hbarAmount: int | None = None
    senderAccountId: str | None = None
    signerNonce: int | None = None
    rawResult: str | None = None


@dataclass
class ContractByteCodeResponse:
    """Response payload for contractByteCodeQuery."""

    contractId: str | None = None
    bytecode: str | None = None


@dataclass
class ContractInfoResponse:
    """Response payload for contractInfoQuery."""

    contractId: str | None = None
    accountId: str | None = None
    contractAccountId: str | None = None
    adminKey: str | None = None
    expirationTime: str | None = None
    autoRenewPeriod: str | None = None
    autoRenewAccountId: str | None = None
    storage: str | None = None
    contractMemo: str | None = None
    balance: str | None = None
    isDeleted: bool | None = None
    maxAutomaticTokenAssociations: str | None = None
    ledgerId: str | None = None
    stakingInfo: StakingInfoResponse | None = None


@dataclass
class StakingInfoResponse:
    """Represent stakingInfoResponse for contractInfoQuery."""

    declineStakingReward: bool | None = None
    stakePeriodStart: str | None = None
    pendingReward: str | None = None
    stakedToMe: str | None = None
    stakedAccountId: str | None = None
    stakedNodeId: str | None = None
