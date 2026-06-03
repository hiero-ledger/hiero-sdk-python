"""TCK request parameter models for account endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseParams, BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
    to_int,
)


@dataclass
class CreateAccountParams(BaseTransactionParams):
    """Request parameters for the createAccount endpoint."""

    key: str | None = None
    initialBalance: int | None = None
    receiverSignatureRequired: bool | None = None
    maxAutoTokenAssociations: int | None = None
    stakedAccountId: str | None = None
    stakedNodeId: int | None = None
    declineStakingReward: bool | None = None
    memo: str | None = None
    autoRenewPeriod: int | None = None
    alias: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateAccountParams:
        """Parse JSON-RPC params into a CreateAccountParams instance."""
        return cls(
            key=params.get("key"),
            initialBalance=to_int(params.get("initialBalance")),
            receiverSignatureRequired=to_bool(params.get("receiverSignatureRequired")),
            maxAutoTokenAssociations=to_int(params.get("maxAutoTokenAssociations")),
            stakedAccountId=params.get("stakedAccountId"),
            stakedNodeId=to_int(params.get("stakedNodeId")),
            declineStakingReward=to_bool(params.get("declineStakingReward")),
            memo=params.get("memo"),
            autoRenewPeriod=to_int(params.get("autoRenewPeriod")),
            alias=params.get("alias"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class UpdateAccountParams(BaseTransactionParams):
    """Request parameters for the updateAccount endpoint."""

    accountId: str | None = None
    key: str | None = None
    receiverSignatureRequired: bool | None = None
    autoRenewPeriod: int | None = None
    expirationTime: int | None = None
    memo: str | None = None
    maxAutoTokenAssociations: int | None = None
    stakedAccountId: str | None = None
    stakedNodeId: int | None = None
    declineStakingReward: bool | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> UpdateAccountParams:
        """Parse JSON-RPC params into an UpdateAccountParams instance."""
        decline_staking_reward = params.get("declineStakingReward")
        if decline_staking_reward is None:
            decline_staking_reward = params.get("declineStakingRewards")

        return cls(
            accountId=params.get("accountId"),
            key=params.get("key"),
            receiverSignatureRequired=to_bool(params.get("receiverSignatureRequired")),
            autoRenewPeriod=to_int(params.get("autoRenewPeriod")),
            expirationTime=to_int(params.get("expirationTime")),
            memo=params.get("memo"),
            maxAutoTokenAssociations=to_int(params.get("maxAutoTokenAssociations")),
            stakedAccountId=params.get("stakedAccountId"),
            stakedNodeId=to_int(params.get("stakedNodeId")),
            declineStakingReward=to_bool(decline_staking_reward),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class DeleteAccountParams(BaseTransactionParams):
    """Request parameters for the deleteAccount endpoint."""

    deleteAccountId: str | None = None
    transferAccountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteAccountParams:
        """Parse JSON-RPC params into a DeleteAccountParams instance."""
        return cls(
            deleteAccountId=params.get("deleteAccountId"),
            transferAccountId=params.get("transferAccountId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class GetAccountInfoParams(BaseParams):
    """Request parameters for the getAccountInfo endpoint."""

    accountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> GetAccountInfoParams:
        """Parse JSON-RPC params into a GetAccountInfoParams instance."""
        return cls(accountId=params.get("accountId"), sessionId=parse_session_id(params))
