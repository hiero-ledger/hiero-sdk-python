"""TCK request parameter models for contract endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_common_transaction_params, parse_session_id


@dataclass
class CreateContractParams(BaseTransactionParams):
    """Parameters for creating a smart contract. Extends BaseTransactionParams to include common transaction parameters."""

    bytecodeFileId: str | None = None
    initcode: str | None = None
    adminKey: str | None = None
    gas: str | None = None
    initialBalance: str | None = None
    constructorParameters: str | None = None
    autoRenewPeriod: str | None = None
    autoRenewAccountId: str | None = None
    memo: str | None = None
    stakedAccountId: str | None = None
    stakedNodeId: str | None = None
    declineStakingReward: bool | None = None
    maxAutomaticTokenAssociations: int | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateContractParams:
        return cls(
            bytecodeFileId=params.get("bytecodeFileId"),
            initcode=params.get("initcode"),
            adminKey=params.get("adminKey"),
            gas=params.get("gas"),
            initialBalance=params.get("initialBalance"),
            constructorParameters=params.get("constructorParameters"),
            autoRenewPeriod=params.get("autoRenewPeriod"),
            autoRenewAccountId=params.get("autoRenewAccountId"),
            memo=params.get("memo"),
            stakedAccountId=params.get("stakedAccountId"),
            stakedNodeId=params.get("stakedNodeId"),
            declineStakingReward=params.get("declineStakingReward"),
            maxAutomaticTokenAssociations=params.get("maxAutomaticTokenAssociations"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
