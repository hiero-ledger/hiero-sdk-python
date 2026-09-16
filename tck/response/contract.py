from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.contract.contract_log_info import ContractLogInfo


@dataclass
class CreateContractResponse:
    """Response payload for createContract."""

    contractId: str | None = None
    status: str | None = None


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
