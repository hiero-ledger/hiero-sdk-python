"""TCK request parameter models for contract endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseParams, BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
)


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


@dataclass
class ContractCallQueryParams(BaseParams):
    """Parameters for contractCallQuery."""

    contractId: str | None = None
    gas: str | None = None
    functionParameters: str | None = None
    maxResultSize: str | None = None
    senderAccountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> ContractCallQueryParams:
        return cls(
            contractId=params.get("contractId"),
            gas=params.get("gas"),
            functionParameters=params.get("functionParameters"),
            maxResultSize=params.get("maxResultSize"),
            senderAccountId=params.get("senderAccountId"),
            sessionId=parse_session_id(params),
        )


@dataclass
class ContractByteCodeQueryParams(BaseParams):
    """Parameters for querying a contract's bytecode."""

    contractId: str | None = None
    queryPayment: str | None = None
    maxQueryPayment: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> ContractByteCodeQueryParams:
        return cls(
            sessionId=parse_session_id(params),
            contractId=params.get("contractId"),
            queryPayment=params.get("queryPayment"),
            maxQueryPayment=params.get("maxQueryPayment"),
        )


@dataclass
class ContractInfoQueryParams(BaseParams):
    """Parameters for contractInfoQuery."""

    contractId: str | None = None
    queryPayment: str | None = None
    maxQueryPayment: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> ContractInfoQueryParams:
        return cls(
            contractId=params.get("contractId"),
            queryPayment=params.get("queryPayment"),
            maxQueryPayment=params.get("maxQueryPayment"),
            sessionId=parse_session_id(params),
        )


@dataclass
class DeleteContractParams(BaseTransactionParams):
    """Parameters for deleting a smart contract. Extends BaseTransactionParams to include common transaction parameters."""

    contractId: str | None = None
    transferAccountId: str | None = None
    transferContractId: str | None = None
    permanentRemoval: bool | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteContractParams:
        return cls(
            contractId=params.get("contractId"),
            transferAccountId=params.get("transferAccountId"),
            transferContractId=params.get("transferContractId"),
            permanentRemoval=to_bool(params.get("permanentRemoval")),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
